# Q31) 코루틴

코루틴(coroutine)은 실행 도중 멈췄다가 나중에 멈춘 자리부터 다시 이어서 실행할 수 있는 작업 단위입니다. 코틀린에서는 멈추는 것을 **일시 중단(suspend)**, 다시 이어 가는 것을 **재개(resume)** 라고 부릅니다.

네트워크 요청이나 파일 읽기처럼 기다리는 시간이 긴 작업을 생각해 보면 쓸모가 보입니다. 일반 함수로 기다리면 결과가 올 때까지 그 스레드가 아무것도 못 하고 묶여 있습니다(블로킹). 코루틴은 기다리는 동안 일시 중단되고, 그동안 스레드는 다른 일을 합니다. 결과가 오면 코루틴이 재개되어 다음 줄부터 이어서 실행됩니다. 그래서 비동기 코드를 콜백 없이 위에서 아래로 읽히는 순서대로 쓸 수 있습니다.

코루틴은 언어와 라이브러리가 나눠서 만듭니다. 컴파일러는 `suspend` 함수를 일시 중단·재개가 가능한 형태로 바꾸는 일만 하고, `launch`·`async` 같은 실제 도구는 `kotlinx.coroutines` 라이브러리가 제공합니다. 아래 예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0에서 실행한 결과입니다.

## 일시 중단과 재개 {#suspend-resume}

코루틴 두 개를 스레드 하나에서 돌려 보면 일시 중단이 무엇인지 바로 보입니다.

```kotlin
// Interleave.kt
import kotlinx.coroutines.*

fun t() = Thread.currentThread().name

fun main() = runBlocking {
    launch { repeat(3) { println("A$it [${t()}]"); delay(10) } }
    launch { repeat(3) { println("B$it [${t()}]"); delay(10) } }
}
```

```text
A0 [main]
B0 [main]
A1 [main]
B1 [main]
A2 [main]
B2 [main]
```

두 코루틴 모두 `main` 스레드 하나에서 돌지만 출력은 번갈아 나옵니다. A가 `delay(10)`에서 일시 중단되면 `main` 스레드가 비고, 그 사이 B가 실행됩니다. B도 `delay`에서 일시 중단되면 10ms가 지난 A가 멈춘 자리부터 재개됩니다.

여기서 `delay`는 `Thread.sleep`과 다릅니다. `Thread.sleep`은 스레드를 붙잡은 채 기다리지만, `delay`는 코루틴만 멈추고 스레드는 놓아줍니다. 재개될 때는 같은 스레드일 수도 있고 다른 스레드일 수도 있습니다. 어느 스레드에서 재개될지는 디스패처가 정하는데, 이 예제처럼 `runBlocking` 안이면 처음 스레드로 돌아옵니다.

## 스레드와의 차이 {#vs-thread}

코루틴은 스레드 위에서 실행되지만 스레드 자체는 아닙니다. 차이는 두 가지입니다.

**가볍습니다.** 스레드는 하나마다 운영체제 자원과 전용 스택 메모리가 필요해서 수만 개를 만들기 어렵습니다. 코루틴은 일시 중단될 때 다음에 이어 갈 위치와 지역 변수 정도만 객체에 담아 두면 되므로, 적은 수의 스레드 위에서 아주 많이 돌릴 수 있습니다.

```kotlin
// Many.kt
fun main() = runBlocking {
    val ms = measureTimeMillis {
        val jobs = List(100_000) { launch { delay(1000L) } }
        jobs.joinAll()
    }
    println("100000 coroutines done in ${ms}ms")
}
```

코루틴 10만 개가 각자 1초씩 기다리는데, 전부 `main` 스레드 하나에서 약 1.1초 만에 끝났습니다. 모두 같은 1초를 동시에 기다렸기 때문입니다.

**스스로 양보합니다.** 운영체제는 스레드를 아무 때나 멈추고 다른 스레드로 바꿀 수 있습니다(선점형). 코루틴은 `delay`나 다른 `suspend` 함수를 부르는 지점에서만 멈춥니다. 각 코루틴이 멈출 지점에서 스스로 실행을 넘기는 방식이라 협력적 멀티태스킹(cooperative multitasking)이라고 부릅니다. 반대로 말하면, 일시 중단 지점 없이 오래 계산만 하는 코루틴은 그동안 스레드를 내주지 않습니다.

## suspend 함수 {#suspend-function}

일시 중단될 수 있는 함수에는 `suspend`를 붙입니다.

```kotlin
// SuspendFunction.kt
suspend fun fetchData(): String {
    delay(1000L)   // 네트워크 지연 흉내
    return "Data fetched"
}

fun main() = runBlocking {
    val result = fetchData()
    println(result)   // Data fetched
}
```

`fetchData`는 `delay`에서 1초 동안 일시 중단되었다가 재개되어 문자열을 돌려줍니다. 호출하는 쪽에서는 일반 함수처럼 결과를 받아 다음 줄에서 씁니다.

`suspend` 함수는 다른 `suspend` 함수나 코루틴 안에서만 부를 수 있습니다. 일반 함수에서 부르면 컴파일 오류가 납니다.

```kotlin
// Normal.kt
fun normal() {
    delay(1)
    // error: suspend function 'suspend fun delay(timeMillis: Long): Unit'
    //        can only be called from a coroutine or another suspend function.
}
```

일시 중단하려면 "어디서 다시 이어 갈지"를 넘겨받을 곳이 필요한데, 일반 함수에는 그런 것이 없기 때문입니다. 컴파일러는 `suspend` 함수마다 보이지 않는 파라미터 하나(`Continuation`)를 더 붙여서 이 정보를 넘깁니다. 자세한 구조는 Q32에서 다룹니다.

## 코루틴 빌더 {#builders}

일반 코드에서 코루틴을 시작하는 함수를 코루틴 빌더라고 합니다. 자주 쓰는 셋은 모두 `kotlinx.coroutines`에 있습니다.

| 빌더 | 돌려주는 것 | 용도 |
|---|---|---|
| `launch` | `Job` | 결과가 필요 없는 작업을 시작합니다. `Job`으로 취소하거나 끝나기를 기다릴 수 있습니다 |
| `async` | `Deferred<T>` | 결과가 필요한 작업을 시작합니다. `await()`로 결과를 받습니다 |
| `runBlocking` | 블록의 결과 | 코루틴이 모두 끝날 때까지 **현재 스레드를 막고** 기다립니다. `main` 함수나 테스트처럼 일반 코드와 코루틴을 잇는 곳에서만 씁니다 |

```kotlin
// LaunchExample.kt
fun main() = runBlocking {
    launch {
        delay(1000L)
        println("Hello from Coroutine! [${t()}]")
    }
    println("Hello from Main! [${t()}]")
}
```

```text
Hello from Main! [main]
Hello from Coroutine! [main]
```

`launch`는 코루틴을 시작만 하고 바로 돌아오므로 `Hello from Main!`이 먼저 찍힙니다. 1초 뒤 코루틴이 재개되어 두 번째 줄을 찍고, `runBlocking`은 안에서 시작한 코루틴이 모두 끝난 뒤에야 `main`을 끝냅니다.

두 줄 모두 `main` 스레드에서 실행된 점도 눈여겨볼 만합니다. `launch`를 썼다고 해서 백그라운드 스레드로 가는 것은 아닙니다. 어느 스레드에서 돌지는 디스패처가 정하고, 따로 지정하지 않으면 바깥 코루틴(여기서는 `runBlocking`)의 것을 이어받습니다.

`async`는 여러 작업을 동시에 시작해 놓고 결과를 모을 때 씁니다.

```kotlin
// AsyncExample.kt
fun main() = runBlocking {
    val a = async { delay(500); 1 }
    val b = async { delay(500); 2 }
    println("sum=${a.await() + b.await()}")   // sum=3, 약 500ms 소요
}
```

두 작업이 동시에 기다리므로 1초가 아니라 약 500ms 만에 끝납니다.

`launch`와 `async`는 `CoroutineScope`의 확장 함수라서 스코프 안에서만 부를 수 있습니다. 그래서 코루틴을 시작하는 함수를 따로 만들려면 스코프를 수신 객체로 받아야 합니다.

```kotlin
// AsyncFunction.kt
fun CoroutineScope.doSomethingAsync() = async { 42 }   // 컴파일됨

fun doSomethingAsync2() = async { 42 }
// error: 'async' can not be called without the corresponding coroutine scope.
```

스코프는 시작한 코루틴들을 묶어서 관리하는 단위입니다. 부모가 자식이 끝나기를 기다리고, 부모를 취소하면 자식도 함께 취소되는 구조화된 동시성(structured concurrency)이 이 스코프를 통해 이루어집니다. 스코프와 `Job`, 디스패처는 뒤의 토픽에서 이어집니다.

## 언어와 라이브러리의 역할 분담 {#language-vs-library}

컴파일러가 코루틴을 위해 직접 지원하는 것은 세 가지뿐입니다. `suspend` 함수, `suspend` 람다, 그리고 그 타입인 `suspend () -> T` 같은 `suspend` 함수 타입입니다. 다른 언어처럼 `async`나 `yield`를 키워드로 두지 않고, 나머지는 모두 함수로 만듭니다.

표준 라이브러리(kotlin-stdlib)에도 코루틴 도구가 조금 있습니다. 가장 익숙한 것이 Q27의 `sequence { }` 빌더입니다.

```kotlin
// SequenceBuilder.kt (kotlin-stdlib 2.4.21)
public fun <T> sequence(@BuilderInference block: suspend SequenceScope<T>.() -> Unit): Sequence<T> =
    Sequence { iterator(block) }
```

`block`의 타입이 `suspend` 람다입니다. `yield(값)`을 부르면 코루틴이 값을 내놓고 일시 중단되었다가, 다음 값을 요청받으면 재개됩니다. 그래서 필요한 만큼만 계산됩니다.

```kotlin
// LazySequence.kt
val squares = sequence {
    for (i in 1..10) {
        println("yield ${i * i}")
        yield(i * i)
    }
    println("over")
}
println(squares.take(2).toList())
```

```text
yield 1
yield 4
[1, 4]
```

두 개만 요청했으므로 코루틴은 두 번째 `yield`에서 멈춘 채 끝나고, `over`는 찍히지 않습니다.

`launch`, `async`, `delay`, 디스패처, 스코프는 표준 라이브러리가 아니라 별도 라이브러리인 `kotlinx.coroutines`에 있습니다. 이렇게 나눠 둔 덕분에 언어는 일시 중단이라는 최소한의 장치만 책임지고, 그 위의 동시성 도구는 라이브러리가 언어 버전과 따로 발전시킬 수 있습니다.

## 요약 {#summary}

코루틴은 실행 도중 일시 중단했다가 멈춘 자리부터 재개할 수 있는 작업 단위입니다. 일시 중단되는 동안 스레드를 놓아주므로, 스레드 하나에서도 여러 코루틴이 번갈아 실행되고, 코루틴 10만 개도 가볍게 돌릴 수 있습니다. 코루틴은 `delay` 같은 일시 중단 지점에서만 멈추는 협력적 방식으로 동작합니다.

`suspend` 함수는 다른 `suspend` 함수나 코루틴 안에서만 부를 수 있습니다. 코루틴은 `launch`(`Job` 반환), `async`(`Deferred` 반환, `await`로 결과), `runBlocking`(스레드를 막고 기다림) 같은 빌더로 시작하며, 이 빌더들은 `kotlinx.coroutines` 라이브러리에 있습니다. 빌더가 백그라운드 스레드를 뜻하지는 않으며, 실행 스레드는 디스패처가 정합니다. 컴파일러는 `suspend` 함수·람다·함수 타입만 지원하고 나머지는 라이브러리로 만듭니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 코루틴이 일시 중단되면 스레드는 어떻게 되나요?">

스레드는 풀려나 다른 일을 합니다. `delay`처럼 일시 중단하는 함수는 코루틴만 멈추고 스레드는 붙잡지 않습니다. 그래서 `main` 스레드 하나에서 돌린 두 코루틴이 `delay`를 만날 때마다 번갈아 실행됩니다.

반면 `Thread.sleep`은 스레드 자체를 멈추므로 그동안 같은 스레드의 다른 코루틴도 실행되지 못합니다. 재개되는 스레드는 디스패처가 정하며, 처음과 다른 스레드일 수도 있습니다.

</def>
<def title="Q) 코루틴이 스레드보다 가볍다는 것은 무슨 뜻인가요?">

스레드는 하나마다 운영체제 자원과 전용 스택이 필요해서 많이 만들기 어렵습니다. 코루틴은 일시 중단될 때 이어 갈 위치와 필요한 지역 변수만 객체에 담아 두면 되므로, 적은 수의 스레드 위에서 아주 많이 돌릴 수 있습니다.

실제로 각자 1초씩 기다리는 코루틴 10만 개를 `main` 스레드 하나에서 돌려도 약 1.1초 만에 모두 끝납니다.

</def>
<def title="Q) suspend 함수를 일반 함수에서 부를 수 없는 이유는 무엇인가요?">

일시 중단하려면 나중에 어디서 다시 이어 갈지를 넘겨받을 곳이 있어야 합니다. 컴파일러는 `suspend` 함수마다 이 정보를 담은 `Continuation` 파라미터를 몰래 하나 더 붙이는데, 일반 함수에는 넘겨줄 `Continuation`이 없습니다.

그래서 일반 함수에서 `delay`를 부르면 "can only be called from a coroutine or another suspend function" 오류가 납니다. 일반 코드에서 코루틴 세계로 들어가려면 `runBlocking`이나 스코프의 `launch` 같은 빌더를 거쳐야 합니다.

</def>
<def title="Q) launch 와 async 는 무엇이 다른가요?">

`launch`는 결과가 필요 없는 작업을 시작하고 `Job`을 돌려줍니다. `Job`으로 작업을 취소하거나 끝나기를 기다릴 수 있지만 값은 받을 수 없습니다.

`async`는 결과가 필요한 작업을 시작하고 `Deferred<T>`를 돌려줍니다. `await()`를 부르면 결과가 나올 때까지 일시 중단되었다가 값을 받습니다. 여러 `async`를 먼저 시작해 두고 나중에 `await`하면 작업들이 동시에 진행되어, 500ms 작업 두 개가 약 500ms 만에 끝납니다.

</def>
<def title="Q) launch 를 쓰면 코드가 백그라운드 스레드에서 실행되나요?">

그렇지 않습니다. 실행 스레드는 디스패처가 정하며, 따로 지정하지 않으면 바깥 코루틴의 디스패처를 이어받습니다. `runBlocking` 안에서 `launch`한 코루틴은 `main` 스레드에서 실행됩니다.

`launch`가 하는 일은 새 코루틴을 시작하고 바로 돌아오는 것입니다. 다른 스레드에서 돌리고 싶으면 `launch(Dispatchers.Default)`처럼 디스패처를 지정해야 합니다.

</def>
</deflist>
