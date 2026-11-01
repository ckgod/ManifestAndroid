# Details: 코루틴과 가변 상태

코루틴 설계 문서(KEEP의 [coroutines 제안서](https://github.com/Kotlin/KEEP/blob/master/proposals/coroutines.md#concurrency-and-threads))는 코루틴 하나하나가 스레드처럼 순차적으로 실행된다고 설명합니다. 이 말에서 두 가지가 나옵니다. 코루틴 하나 안에서는 `mutableMapOf` 같은 일반 가변 객체를 안심하고 써도 되고, 여러 코루틴이 같은 가변 객체를 함께 고칠 때는 스레드와 똑같이 조심해야 한다는 것입니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했습니다.

## 코루틴 하나 안의 순차 실행 {#sequential}

코루틴 안의 코드는 적힌 순서대로 한 줄씩 실행됩니다. 일시 중단 지점을 지나면서 실행 스레드가 바뀌더라도 순서는 그대로입니다.

```kotlin
// Sequential.kt
import kotlinx.coroutines.*

fun t() = Thread.currentThread().name

fun main() = runBlocking<Unit> {
    launch(Dispatchers.Default) {
        val m = mutableMapOf<String, String>()
        val v1 = async(Dispatchers.IO) { delay(100); "값1" }
        val v2 = async(Dispatchers.IO) { delay(50); "값2" }
        m["k1"] = v1.await(); println("k1 저장 [${t()}]")
        m["k2"] = v2.await(); println("k2 저장 [${t()}]")
        withContext(Dispatchers.IO) { m["k3"] = "값3"; println("k3 저장 [${t()}]") }
        println("$m [${t()}]")
    }
}
```

```text
k1 저장 [DefaultDispatcher-worker-3]
k2 저장 [DefaultDispatcher-worker-3]
k3 저장 [DefaultDispatcher-worker-3]
{k1=값1, k2=값2, k3=값3} [DefaultDispatcher-worker-1]
```

`v1`, `v2`는 다른 코루틴에서 동시에 계산되지만, 맵 `m`을 고치는 것은 바깥 코루틴 하나뿐입니다. 이 코루틴은 `await`에서 일시 중단되었다가 재개되고, 이번 실행에서는 마지막 줄이 처음과 다른 스레드(`worker-1`)에서 실행되었습니다. 어느 스레드에서 재개될지는 실행할 때마다 달라집니다. 그래도 `m`에 대한 쓰기는 한 번에 하나씩, 적힌 순서대로 일어났고 결과도 맞습니다.

스레드가 바뀌었는데도 동기화 없이 안전한 이유는 재개 과정 자체가 동기화를 거치기 때문입니다. 디스패처는 재개할 코루틴을 스레드 간 공유 작업 큐에 넣고, 다른 스레드가 그 큐에서 꺼내 실행합니다. 이 큐는 넣기 전에 쓴 값이 꺼낸 뒤에 보이도록 보장하므로(<tooltip term="Happens_Before">happens-before</tooltip> 관계), 일시 중단 전에 쓴 값은 다른 스레드에서 재개된 뒤에도 그대로 보입니다. 그래서 코루틴 하나만 쓰는 가변 객체는 스레드가 바뀌어도 `ConcurrentHashMap`이나 락 없이 써도 됩니다. `m`이 이 코루틴 안의 지역 변수라서 다른 코루틴이 건드릴 방법이 없다는 점이 중요합니다.

## 여러 코루틴의 상태 공유 {#shared}

여러 코루틴이 같은 변수를 고치고, 그 코루틴들이 여러 스레드에서 동시에 실행되면 스레드에서와 똑같은 레이스 컨디션이 생깁니다. `Dispatchers.Default`에서 코루틴 1,000개가 각각 1,000번씩 숫자를 1 올려 봤습니다. 맞다면 1,000,000이 나와야 합니다.

```kotlin
// Race.kt
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.*
import java.util.concurrent.atomic.AtomicInteger

suspend fun massiveRun(action: suspend () -> Unit) = coroutineScope {
    repeat(1000) { launch { repeat(1000) { action() } } }
}

fun main() = runBlocking {
    var plain = 0
    withContext(Dispatchers.Default) { massiveRun { plain++ } }
    println("보호 없음: $plain")

    val atomic = AtomicInteger()
    withContext(Dispatchers.Default) { massiveRun { atomic.incrementAndGet() } }
    println("AtomicInteger: ${atomic.get()}")

    val mutex = Mutex()
    var locked = 0
    withContext(Dispatchers.Default) { massiveRun { mutex.withLock { locked++ } } }
    println("Mutex: $locked")

    val single = Dispatchers.Default.limitedParallelism(1)
    var confined = 0
    withContext(Dispatchers.Default) { massiveRun { withContext(single) { confined++ } } }
    println("limitedParallelism(1): $confined")
}
```

```text
보호 없음: 109088
AtomicInteger: 1000000
Mutex: 1000000
limitedParallelism(1): 1000000
```

보호 없이 올린 값은 1,000,000에 한참 못 미쳤고, 다시 실행하니 284,489가 나왔습니다. 실행할 때마다 달라집니다. `plain++`는 "읽기, 1 더하기, 쓰기" 세 단계인데, 두 스레드가 같은 값을 읽고 각자 1을 더해 쓰면 한 번이 사라지기 때문입니다.

결과를 맞춘 세 가지 방법은 다음과 같습니다.

- **원자적 변수(`AtomicInteger` 등).** 읽기·더하기·쓰기를 CPU가 끊기지 않는 한 동작으로 처리합니다. 숫자 하나나 참조 하나처럼 단순한 값에 맞습니다.
- **`Mutex`.** 코루틴용 락입니다. `withLock` 블록에는 한 번에 한 코루틴만 들어갑니다. 자바의 `synchronized`와 달리 락을 기다리는 동안 스레드를 막지 않고 코루틴만 일시 중단합니다. 여러 값을 함께 고쳐야 할 때 씁니다.
- **한 스레드에 가두기.** `limitedParallelism(1)`처럼 한 번에 하나씩만 실행하는 디스패처에서만 상태를 고치면, 동시에 고치는 일 자체가 생기지 않습니다.

`ConcurrentHashMap` 같은 동시성 컬렉션도 쓸 수 있습니다. 다만 메서드 하나하나가 안전할 뿐이라 "읽고 나서 조건에 따라 쓰기"처럼 여러 호출을 묶은 동작은 따로 보호해야 합니다.

## 단일 스레드 디스패처와 일시 중단 지점 {#single-thread}

책은 `Dispatchers.Main`처럼 스레드 하나에서만 도는 디스패처라면 공유 가변 객체를 안전하게 고칠 수 있다고 설명합니다. 동시에 두 스레드가 접근하는 일이 없으니 앞의 `plain++` 같은 문제는 생기지 않습니다. 자바스크립트가 이벤트 루프 하나로 도는 것과 비슷합니다.

그런데 읽기와 쓰기 사이에 일시 중단 지점이 끼면 스레드가 하나여도 결과가 깨집니다.

```kotlin
// SingleThreadLost.kt
import kotlinx.coroutines.*

fun main() = runBlocking {          // main 스레드 하나만 씁니다
    var count = 0
    val jobs = List(100) {
        launch {
            val current = count     // 1. 읽고
            delay(1)                // 2. 일시 중단 (다른 코루틴이 실행됨)
            count = current + 1     // 3. 읽었던 값으로 씀
        }
    }
    jobs.joinAll()
    println("count = $count")
}
```

```text
count = 1
```

100번 올렸는데 1이 나왔습니다. 100개 코루틴이 모두 `count`가 0일 때 값을 읽고 `delay`에서 일시 중단되었고, 재개된 뒤 각자 `0 + 1`을 썼기 때문입니다. 스레드가 하나라서 동시에 실행된 순간은 없었지만, 일시 중단 지점에서 다른 코루틴이 끼어들 수 있으므로 "읽고 나서 쓰기까지"가 한 덩어리로 실행된다는 보장이 없습니다.

안드로이드에서도 같은 일이 생깁니다. `viewModelScope`(기본이 `Dispatchers.Main`)에서 상태 값을 읽고, 네트워크 요청을 `await`한 뒤, 처음 읽은 값을 바탕으로 상태를 덮어쓰면 그 사이 다른 코루틴이 바꾼 내용이 사라질 수 있습니다. 쓰기 직전에 최신 값을 다시 읽거나(`MutableStateFlow.update { }`가 이렇게 동작합니다), 읽기부터 쓰기까지를 `Mutex`로 묶어야 합니다.

## 요약 {#summary}

코루틴 하나 안의 코드는 일시 중단을 거쳐 스레드가 바뀌어도 적힌 순서대로 실행되고, 재개 과정이 동기화를 거쳐 메모리 가시성이 맞춰지므로 그 코루틴만 쓰는 가변 객체는 동기화 없이 써도 됩니다.

여러 코루틴이 여러 스레드에서 같은 가변 상태를 고치면 레이스 컨디션이 생깁니다. 원자적 변수, `Mutex`, 한 스레드에 가두기(`limitedParallelism(1)`) 중 하나로 막습니다. 스레드 하나에서만 도는 디스패처라도 읽기와 쓰기 사이에 일시 중단 지점이 있으면 다른 코루틴이 끼어들 수 있으므로, 그 구간은 한 덩어리로 묶어야 합니다.
