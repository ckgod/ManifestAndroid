# Q34) 코루틴 빌더

코루틴 빌더는 일반 코드에서 코루틴을 만들고 시작하는 함수입니다. Q31에서 `launch`, `async`, `runBlocking`을 짧게 봤습니다. 이 토픽에서는 다섯 빌더(`launch`, `async`, `runBlocking`, `produce`, `actor`)가 공통으로 거치는 네 단계를 먼저 보고, 빌더마다 무엇을 돌려주고 안에서 어떤 객체를 만드는지 차례로 봅니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했습니다. 라이브러리 내부 코드도 같은 버전의 소스에서 옮겼습니다.

## 빌더의 공통 구조 {#common-structure}

`launch`의 실제 소스는 열 줄 남짓입니다.

```kotlin
// Builders.common.kt (kotlinx-coroutines 1.11.0)
public fun CoroutineScope.launch(
    context: CoroutineContext = EmptyCoroutineContext,
    start: CoroutineStart = CoroutineStart.DEFAULT,
    block: suspend CoroutineScope.() -> Unit
): Job {
    val newContext = newCoroutineContext(context)          // 1. 컨텍스트 합치기
    val coroutine = if (start.isLazy)                      // 2. 코루틴 객체 만들기
        LazyStandaloneCoroutine(newContext, block) else
        StandaloneCoroutine(newContext, active = true)
    coroutine.start(start, coroutine, block)               // 3. 실행 시작
    return coroutine                                       // 4. 코루틴 객체를 그대로 돌려주기
}
```

다른 빌더도 이 네 단계를 그대로 따릅니다.

1. **컨텍스트 합치기.** 부모 스코프의 컨텍스트에 인자로 받은 `context`를 더해 새 코루틴의 컨텍스트를 만듭니다.
2. **코루틴 객체 만들기.** 빌더마다 만드는 클래스가 다릅니다. `start`가 `LAZY`면 바로 실행되지 않는 별도 클래스를 씁니다.
3. **실행 시작.** `start` 방식에 따라 블록 실행을 디스패처에 맡기거나, 나중에 시작할 준비만 해 둡니다.
4. **코루틴 객체 반환.** 코루틴 객체가 `Job`(또는 `Deferred`, 채널) 인터페이스를 직접 구현하므로, 만든 객체를 그대로 돌려주면 그것이 호출한 쪽이 쓰는 핸들(손잡이)이 됩니다.

빌더마다 2단계에서 만드는 클래스와 4단계에서 돌려주는 타입은 이렇습니다.

| 빌더 | 만드는 코루틴 클래스 | 반환 타입 | 블록의 수신 객체 |
|---|---|---|---|
| `launch` | `StandaloneCoroutine` / `LazyStandaloneCoroutine` | `Job` | `CoroutineScope` |
| `async` | `DeferredCoroutine` / `LazyDeferredCoroutine` | `Deferred<T>` | `CoroutineScope` |
| `runBlocking` | `BlockingCoroutine` | 블록의 결과 `T` | `CoroutineScope` |
| `produce` | `ProducerCoroutine` | `ReceiveChannel<E>` | `ProducerScope<E>` |
| `actor` | `ActorCoroutine` / `LazyActorCoroutine` | `SendChannel<E>` | `ActorScope<E>` |

이 클래스들은 모두 `AbstractCoroutine`을 상속합니다. 하나의 객체가 `Job`이면서 블록이 끝났을 때 결과를 받는 `Continuation`이기도 한 구조인데, 자세한 내용은 [AbstractCoroutine의 내부 구조](Details-AbstractCoroutine의-내부-구조.md)에서 다룹니다.

`runBlocking`을 뺀 네 빌더는 `CoroutineScope`의 확장 함수입니다. 부모 스코프가 있어야 1단계에서 부모 컨텍스트를 이어받을 수 있기 때문입니다. `runBlocking`은 일반 함수라서 스코프 없이 어디서나 부를 수 있고, 그 대신 부모가 없는 최상위 코루틴을 만듭니다.

## 컨텍스트 합치기 {#new-context}

1단계의 `newCoroutineContext(context)`는 부모 스코프의 컨텍스트와 인자로 받은 `context`를 합칩니다. 같은 종류의 요소가 양쪽에 있으면 인자 쪽이 이깁니다.

```kotlin
// ContextInherit.kt
import kotlinx.coroutines.*

fun threadName(): String = Thread.currentThread().name

fun CoroutineScope.describe(label: String) {
    println("$label 이름=${coroutineContext[CoroutineName]?.name}, 스레드=${threadName()}")
}

fun main() = runBlocking<Unit>(CoroutineName("부모")) {
    // 1. 아무것도 넘기지 않으면 부모 컨텍스트를 그대로 이어받습니다
    launch { describe("1)") }.join()

    // 2. 넘긴 요소만 덮어씁니다. 디스패처만 바꿨으므로 이름은 그대로입니다
    launch(Dispatchers.Default) { describe("2)") }.join()

    // 3. 이름만 바꾸면 디스패처는 부모 것을 씁니다
    launch(CoroutineName("자식")) { describe("3)") }.join()

    // 4. 새 코루틴의 Job 은 부모 Job 의 자식으로 등록됩니다
    val parentJob = coroutineContext[Job]
    val child = launch { delay(100) }
    println("4) runBlocking 의 자식 목록에 있나요? ${parentJob?.children?.contains(child)}")
}
```

```text
1) 이름=부모, 스레드=main
2) 이름=부모, 스레드=DefaultDispatcher-worker-1
3) 이름=자식, 스레드=main
4) runBlocking 의 자식 목록에 있나요? true
```

`Job`만은 다르게 다뤄집니다. 부모의 `Job`을 그대로 쓰지 않고, 새로 만든 코루틴 객체 자신이 새 `Job`이 되어 부모 `Job`의 자식으로 등록됩니다. 이 부모·자식 연결 덕분에 부모가 자식을 기다리고, 부모를 취소하면 자식도 취소되는 구조화된 동시성(structured concurrency)이 성립합니다. 연결은 코루틴이 끝나면 풀리므로, 자식이 끝난 뒤에 확인하면 부모의 `children`에서 빠져 있습니다.

책에는 없지만 JVM의 `newCoroutineContext`는 한 가지를 더 합니다. 합친 결과에 디스패처가 하나도 없으면 `Dispatchers.Default`를 붙입니다.

```kotlin
// DefaultDispatcher.kt
import kotlinx.coroutines.*

fun threadName(): String = Thread.currentThread().name

fun main() {
    // 디스패처가 없는 스코프에서 launch 합니다
    val scope = CoroutineScope(Job())
    val job = scope.launch {
        println("스레드=${threadName()}")
    }
    runBlocking { job.join() }
}
```

```text
스레드=DefaultDispatcher-worker-1
```

그래서 디스패처를 지정하지 않은 스코프에서 시작한 코루틴은 `Dispatchers.Default`의 스레드에서 실행됩니다.

## 시작 방식 {#coroutine-start}

`launch`, `async`, `actor`는 `start` 파라미터로 코루틴을 언제, 어떻게 시작할지 정합니다.

| 값 | 동작 |
|---|---|
| `DEFAULT` | 기본값입니다. 만들자마자 블록 실행을 디스패처에 맡깁니다 |
| `LAZY` | 만들기만 하고 실행하지 않습니다. `start()`, `join()`, `await()`를 부를 때 시작합니다 |
| `ATOMIC` | `DEFAULT`와 같지만, 실행이 시작되기 전에는 취소되지 않습니다 |
| `UNDISPATCHED` | 디스패처를 거치지 않고 지금 스레드에서 첫 일시 중단 지점까지 바로 실행합니다 |

`LAZY`로 만든 코루틴은 누군가 시작시킬 때까지 실행되지 않습니다.

```kotlin
// LazyStart.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val job = launch(start = CoroutineStart.LAZY) {
        println("코루틴 본문 실행")
    }
    println("만든 직후: isActive=${job.isActive}")

    delay(100)
    println("100ms 뒤에도 실행되지 않음")

    job.start()   // 여기서 비로소 실행이 예약됩니다
    job.join()
    println("start 후: isCompleted=${job.isCompleted}")
}
```

```text
만든 직후: isActive=false
100ms 뒤에도 실행되지 않음
코루틴 본문 실행
start 후: isCompleted=true
```

`launch`가 `LAZY`일 때 만드는 `LazyStandaloneCoroutine`은 이렇게 생겼습니다.

```kotlin
// Builders.common.kt (kotlinx-coroutines 1.11.0)
private class LazyStandaloneCoroutine(
    parentContext: CoroutineContext,
    block: suspend CoroutineScope.() -> Unit
) : StandaloneCoroutine(parentContext, active = false) {
    // 블록을 실행할 준비만 해 둡니다. 디스패처에 맡기지는 않습니다
    private val continuation = block.createCoroutineUnintercepted(this, this)

    // start() 나 join() 이 처음 불릴 때 호출됩니다
    override fun onStart() {
        continuation.startCoroutineCancellable(this)
    }
}
```

`active = false`로 만들기 때문에 처음 상태가 "아직 시작 안 함"(New)이고, 위 예제에서 `isActive`가 `false`로 나온 것이 그 때문입니다. 생성자에서 `createCoroutineUnintercepted`로 블록의 첫 `Continuation`(Q32에서 본 상태 객체)을 만들어 두기만 하고, `onStart`가 불릴 때 그것을 실행에 넘깁니다.

## launch {#launch}

`launch`는 결과를 돌려주지 않는 코루틴을 시작합니다. 화면 갱신, 로그 전송, DB 저장처럼 일을 시켜 두고 결과를 기다리지 않는 작업에 씁니다. 이런 방식을 영어로 fire-and-forget(쏘고 잊기)이라고 부릅니다.

```kotlin
// LaunchBasic.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val job: Job = launch {
        delay(1000L)
        println("작업 완료")
    }
    println("launch 는 바로 돌아옵니다. isActive=${job.isActive}")
    job.join()   // 끝날 때까지 기다릴 수는 있지만, 결과 값은 받을 수 없습니다
    println("join 후: isCompleted=${job.isCompleted}")
}
```

```text
launch 는 바로 돌아옵니다. isActive=true
작업 완료
join 후: isCompleted=true
```

돌려받은 `Job`으로는 상태 확인(`isActive`, `isCompleted`), 완료 대기(`join()`), 취소(`cancel()`)를 할 수 있습니다. 블록의 타입이 `suspend CoroutineScope.() -> Unit`이라 블록 마지막 줄에 값이 있어도 버려집니다.

`launch`가 만드는 `StandaloneCoroutine`은 예외 처리 하나만 정의합니다.

```kotlin
// Builders.common.kt (kotlinx-coroutines 1.11.0)
private open class StandaloneCoroutine(
    parentContext: CoroutineContext,
    active: Boolean
) : AbstractCoroutine<Unit>(parentContext, initParentJob = true, active = active) {
    override fun handleJobException(exception: Throwable): Boolean {
        handleCoroutineException(context, exception)
        return true
    }
}
```

`AbstractCoroutine<Unit>`을 상속하므로 결과 값이 없습니다. 코루틴이 잡히지 않은 예외로 끝나면 먼저 부모를 취소하며 예외를 알립니다. 부모가 다른 코루틴이면 예외 처리도 부모가 이어받아 위로 올려 보내고, 위에 예외를 맡을 코루틴이 없을 때(`CoroutineScope(Job())`처럼 직접 만든 스코프 바로 아래이거나, 부모가 `SupervisorJob`일 때)만 `handleJobException`이 불립니다. 여기서 부르는 `handleCoroutineException`은 컨텍스트의 `CoroutineExceptionHandler`에, 없으면 스레드의 기본 예외 처리기에 예외를 보고합니다. 안드로이드에서 `launch` 안의 예외가 앱을 종료시키는 것이 이 경로입니다. `async`와의 차이는 [launch와 async의 차이](Details-launch와-async의-차이.md)에서 예제로 봅니다.

## async {#async}

`async`는 결과를 돌려주는 코루틴을 시작하고, 그 결과를 나중에 받을 수 있는 `Deferred<T>`를 돌려줍니다. 결과는 `await()`로 꺼냅니다. 여러 작업을 동시에 실행하고 결과를 모아야 할 때 씁니다.

```kotlin
// AsyncParallel.kt
import kotlinx.coroutines.*
import kotlin.system.measureTimeMillis

suspend fun fetchUser(): String {
    delay(300)
    return "창국"
}

suspend fun fetchPermissions(): List<String> {
    delay(200)
    return listOf("read", "write")
}

fun main() = runBlocking<Unit> {
    val elapsed = measureTimeMillis {
        val user: Deferred<String> = async { fetchUser() }
        val permissions: Deferred<List<String>> = async { fetchPermissions() }

        // 두 코루틴은 이미 동시에 돌고 있고, await 는 결과가 나올 때까지 기다립니다
        println("사용자=${user.await()}, 권한=${permissions.await()}")
    }
    println("걸린 시간: 약 ${elapsed / 100 * 100}ms")
}
```

```text
사용자=창국, 권한=[read, write]
걸린 시간: 약 300ms
```

두 작업이 동시에 진행되어 300ms와 200ms를 더한 500ms가 아니라 긴 쪽인 300ms 만에 끝났습니다. `await()`는 `suspend` 함수라서 결과를 기다리는 동안 스레드를 막지 않고 코루틴만 일시 중단합니다.

`async`의 소스는 `launch`와 거의 같고, 2단계에서 만드는 클래스만 다릅니다.

```kotlin
// Builders.common.kt (kotlinx-coroutines 1.11.0)
private open class DeferredCoroutine<T>(
    parentContext: CoroutineContext,
    active: Boolean
) : AbstractCoroutine<T>(parentContext, true, active = active), Deferred<T> {
    override fun getCompleted(): T = getCompletedInternal() as T
    override suspend fun await(): T = awaitInternal() as T
    override val onAwait: SelectClause1<T> get() = onAwaitInternal as SelectClause1<T>
}
```

`AbstractCoroutine<T>`를 상속하므로 블록이 끝나면 `T` 타입 결과가 이 객체의 상태로 저장됩니다. `await()`는 부모 클래스의 `awaitInternal()`에 맡기는데, 이 함수는 코루틴이 완료 상태가 될 때까지 부른 쪽을 일시 중단했다가 저장된 결과를 돌려줍니다. 실패로 끝났다면 저장된 예외를 던집니다. `Deferred<T>`는 `Job`을 상속하므로 `join()`, `cancel()`도 그대로 쓸 수 있습니다.

`StandaloneCoroutine`과 달리 `handleJobException`을 정의하지 않습니다. 그래서 `async`의 예외는 `CoroutineExceptionHandler`로 보고되지 않고 `Deferred` 안에 보관되었다가 `await()`에서 던져집니다. 그렇다고 예외가 부모에게 안 가는 것은 아닙니다. 부모가 일반 `Job`이면 `async`가 실패하는 즉시 부모와 형제 코루틴이 취소됩니다. 이 부분은 [launch와 async의 차이](Details-launch와-async의-차이.md)에서 실행 결과로 확인합니다.

`LAZY`로 시작한 `async`는 `await()`가 처음 불릴 때 시작합니다. 이 때문에 위 예제에 `LAZY`만 붙이면 동시에 실행되지 않습니다.

```kotlin
// AsyncLazyTrap.kt
import kotlinx.coroutines.*
import kotlin.system.measureTimeMillis

suspend fun fetchUser(): String {
    delay(300)
    return "창국"
}

suspend fun fetchPermissions(): List<String> {
    delay(200)
    return listOf("read", "write")
}

fun main() = runBlocking<Unit> {
    val elapsed = measureTimeMillis {
        val user = async(start = CoroutineStart.LAZY) { fetchUser() }
        val permissions = async(start = CoroutineStart.LAZY) { fetchPermissions() }

        // await 가 처음 불릴 때 시작되므로, 앞의 것이 끝나야 뒤의 것이 시작됩니다
        println("사용자=${user.await()}, 권한=${permissions.await()}")
    }
    println("걸린 시간: 약 ${elapsed / 100 * 100}ms")
}
```

```text
사용자=창국, 권한=[read, write]
걸린 시간: 약 500ms
```

`user.await()`가 `user`를 시작하고 끝날 때까지 기다린 다음에야 `permissions.await()`가 `permissions`를 시작합니다. 동시에 돌리려면 `await()` 전에 각각 `start()`를 불러야 합니다.

## runBlocking {#run-blocking}

`runBlocking`은 새 코루틴을 만들고, 그 코루틴과 자식들이 모두 끝날 때까지 **자기를 부른 스레드를 막고** 기다립니다. 일반 코드(일반 함수)에서 `suspend` 함수를 부를 수 있게 이어 주는 다리 역할입니다.

```kotlin
// RunBlockingBasic.kt
import kotlinx.coroutines.*

fun threadName(): String = Thread.currentThread().name

fun main() {
    println("runBlocking 전 (${threadName()})")

    val result: Int = runBlocking {
        launch {
            delay(500)
            println("안쪽 launch 완료 (${threadName()})")
        }
        delay(100)
        42   // 블록의 마지막 값이 runBlocking 의 반환 값입니다
    }

    // 안쪽 launch 까지 모두 끝나야 이 줄로 내려옵니다
    println("runBlocking 후: result=$result (${threadName()})")
}
```

```text
runBlocking 전 (main)
안쪽 launch 완료 (main)
runBlocking 후: result=42 (main)
```

블록은 100ms 뒤에 `42`를 내놓았지만, 안쪽 `launch`가 끝나는 500ms까지 `main` 스레드는 다음 줄로 넘어가지 못했습니다. 디스패처를 지정하지 않으면 `runBlocking`은 부른 스레드에서 도는 이벤트 루프(할 일을 하나씩 꺼내 실행하는 반복문)를 만들어 안쪽 코루틴을 모두 그 스레드에서 실행합니다. 출력이 전부 `main`인 이유입니다.

다른 빌더와 달리 `Job`이 아니라 블록의 결과를 바로 돌려주고, 블록이 예외로 끝나면 그 예외를 던집니다. 막혀 있던 스레드가 인터럽트되면 코루틴을 취소하고 `InterruptedException`을 던집니다.

스레드를 막는다는 성질 때문에 `main` 함수나 테스트처럼 일반 코드와 코루틴을 잇는 곳에서만 씁니다. 안드로이드 메인 스레드에서 부르면 그동안 화면이 멈춥니다. 앱 코드에서는 `lifecycleScope.launch`나 `viewModelScope.launch`로 코루틴을 시작합니다. 내부 구현과 써도 되는 경우는 [runBlocking을 신중하게 써야 하는 이유](Details-runBlocking을-신중하게-써야-하는-이유.md)에서 다룹니다.

## produce {#produce}

`produce`는 값을 차례로 만들어 채널(`Channel`)로 내보내는 코루틴을 시작하고, 받는 쪽 채널인 `ReceiveChannel<E>`를 돌려줍니다. 채널은 코루틴 사이에서 값을 주고받는 통로이고, 보내는 쪽은 `send`, 받는 쪽은 `receive`나 `for` 문을 씁니다.

```kotlin
// ProduceBasic.kt
@file:OptIn(ExperimentalCoroutinesApi::class)

import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*

fun main() = runBlocking<Unit> {
    val numbers: ReceiveChannel<Int> = produce {
        for (i in 1..3) {
            send(i)   // ProducerScope 가 SendChannel 이라 바로 send 를 부릅니다
        }
        // 블록이 끝나면 채널이 닫힙니다
    }

    for (value in numbers) {   // 채널이 닫히면 반복문이 끝납니다
        println("받음 $value")
    }
    println("채널이 닫혀 반복문 종료")
}
```

```text
받음 1
받음 2
받음 3
채널이 닫혀 반복문 종료
```

`produce`는 `@ExperimentalCoroutinesApi`가 붙은 실험 API입니다. 부모 스코프 안에서 취소·오류를 처리하는 방식이 앞으로 바뀔 수 있다고 문서에 적혀 있어서, 쓰려면 `@OptIn`을 붙여야 경고가 사라집니다.

내부에서는 1단계보다 먼저 채널을 만듭니다.

```kotlin
// Produce.kt (kotlinx-coroutines 1.11.0)
internal fun <E> CoroutineScope.produce(
    context: CoroutineContext = EmptyCoroutineContext,
    capacity: Int = 0,
    onBufferOverflow: BufferOverflow = BufferOverflow.SUSPEND,
    start: CoroutineStart = CoroutineStart.DEFAULT,
    onCompletion: CompletionHandler? = null,
    block: suspend ProducerScope<E>.() -> Unit
): ReceiveChannel<E> {
    val channel = Channel<E>(capacity, onBufferOverflow)   // 값이 지나갈 채널
    val newContext = newCoroutineContext(context)
    val coroutine = ProducerCoroutine(newContext, channel)  // 코루틴이면서 채널인 객체
    if (onCompletion != null) coroutine.invokeOnCompletion(handler = onCompletion)
    coroutine.start(start, coroutine, block)
    return coroutine
}
```

우리가 부르는 공개 `produce`는 이 내부 함수를 호출하는 얇은 함수입니다. `capacity` 기본값 0은 버퍼가 없는 채널이라, `send`는 받는 쪽이 값을 가져갈 때까지 기다립니다.

`ProducerCoroutine`은 코루틴이면서 채널이기도 한 객체입니다.

```kotlin
// Produce.kt (kotlinx-coroutines 1.11.0)
private class ProducerCoroutine<E>(
    parentContext: CoroutineContext, channel: Channel<E>
) : ChannelCoroutine<E>(parentContext, channel, true, active = true), ProducerScope<E> {

    // 블록이 정상적으로 끝나면: 채널을 닫습니다
    override fun onCompleted(value: Unit) {
        _channel.close()
    }

    // 취소되거나 예외로 끝나면: 원인을 담아 채널을 닫습니다
    override fun onCancelled(cause: Throwable, handled: Boolean) {
        val processed = _channel.close(cause)
        if (!processed && !handled) handleCoroutineException(context, cause)
    }
}
```

- `ChannelCoroutine`은 `Job`과 `Channel`을 함께 구현하는 내부 클래스입니다. 채널 동작은 안에 든 `_channel`에 넘깁니다. 이 객체를 `ReceiveChannel` 타입으로 돌려주므로 받는 쪽은 값을 받을 수만 있고 보낼 수는 없습니다.
- 블록의 수신 객체인 `ProducerScope<E>`는 `CoroutineScope`와 `SendChannel<E>`를 함께 상속합니다. 그래서 `produce { }` 안에서 `send(i)`를 바로 부를 수 있습니다.
- 코루틴의 끝과 채널의 닫힘이 묶여 있습니다. 블록이 정상적으로 끝나면 채널을 닫아 받는 쪽 `for` 문이 끝나고, 예외로 끝나면 그 예외를 원인으로 채널을 닫아 받는 쪽이 같은 예외를 받습니다.

```kotlin
// ProduceFail.kt
@file:OptIn(ExperimentalCoroutinesApi::class)

import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*

fun main() = runBlocking<Unit> {
    supervisorScope {   // 생산자 실패가 부모까지 취소하지 않도록 감쌉니다
        val numbers = produce {
            send(1)
            throw IllegalStateException("생산 실패")
        }

        try {
            for (value in numbers) {
                println("받음 $value")
            }
        } catch (e: IllegalStateException) {
            println("소비자가 받은 예외: ${e.message}")
        }
    }
}
```

```text
받음 1
소비자가 받은 예외: 생산 실패
```

`supervisorScope`로 감싼 이유는 `produce`도 `launch`처럼 실패를 부모에게 넘기기 때문입니다. 감싸지 않으면 생산자의 예외가 `runBlocking`까지 취소해 버립니다.

## actor {#actor}

`actor`는 메시지를 받는 채널(메일박스)을 가진 코루틴을 시작하고, 보내는 쪽 채널인 `SendChannel<E>`를 돌려줍니다. 액터 모델(Actor Model)을 코루틴으로 옮긴 것입니다. 액터 모델은 1973년 칼 휴잇(Carl Hewitt)이 제안한 동시성 모델로, 각 액터가 자기 상태를 혼자 갖고 다른 쪽과는 메시지로만 주고받습니다. 상태를 여러 스레드가 함께 고치지 않으므로 잠금(lock) 없이도 경쟁 상태가 생기지 않습니다.

여러 코루틴이 동시에 카운터를 올리는 예제입니다.

```kotlin
// ActorCounter.kt
@file:OptIn(ObsoleteCoroutinesApi::class)

import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*

// 액터에게 보낼 메시지 종류
sealed interface CounterMessage
object Increment : CounterMessage
class GetCount(val response: CompletableDeferred<Int>) : CounterMessage

fun CoroutineScope.counterActor(): SendChannel<CounterMessage> = actor {
    var count = 0   // 이 변수는 액터 코루틴 안에서만 읽고 씁니다
    for (message in channel) {
        when (message) {
            is Increment -> count++
            is GetCount -> message.response.complete(count)
        }
    }
}

fun main() = runBlocking<Unit> {
    val counter = counterActor()

    // 여러 스레드에서 1,000개 코루틴이 동시에 메시지를 보냅니다
    withContext(Dispatchers.Default) {
        repeat(1_000) {
            launch { counter.send(Increment) }
        }
    }

    val response = CompletableDeferred<Int>()
    counter.send(GetCount(response))
    println("count = ${response.await()}")

    counter.close()   // 메일박스를 닫아야 액터의 for 문이 끝납니다
}
```

```text
count = 1000
```

메시지는 여러 스레드에서 동시에 들어오지만, 메일박스에서 하나씩 꺼내 처리하는 것은 액터 코루틴 하나뿐이라 `count`는 정확히 1000이 됩니다. 값을 돌려받아야 할 때는 `GetCount`처럼 응답용 `CompletableDeferred`를 메시지에 담아 보냅니다. [코루틴과 가변 상태](Details-코루틴과-가변-상태.md)에서 본 `Mutex`와 같은 문제를 다른 방식으로 푸는 셈입니다.

`main`을 `runBlocking<Unit>`으로 쓴 데는 이유가 있습니다. 책의 예제처럼 `fun main() = runBlocking { ...; actor.close() }`로 쓰면 마지막 식 `close()`의 반환 타입 `Boolean`이 `main`의 반환 타입이 되어 `main` 함수로 인식되지 않고 실행되지 않습니다.

`actor`는 `@ObsoleteCoroutinesApi`가 붙어 있고 JVM에서만 쓸 수 있습니다. 라이브러리 문서에는 "더 복잡한 액터가 도입되면 이 API는 낡은 것이 된다"고 적혀 있습니다. 동작은 하지만 새 코드에서 기댈 API는 아니라는 뜻입니다.

내부 구조는 `produce`를 뒤집은 모양입니다.

```kotlin
// Actor.kt (kotlinx-coroutines 1.11.0, 일부 생략)
private open class ActorCoroutine<E>(
    parentContext: CoroutineContext,
    channel: Channel<E>,
    active: Boolean
) : ChannelCoroutine<E>(parentContext, channel, initParentJob = false, active = active), ActorScope<E> {

    init {
        initParentJob(parentContext[Job])
    }

    // 액터가 취소되면 메일박스도 취소합니다
    override fun onCancelling(cause: Throwable?) {
        _channel.cancel(cause?.let {
            it as? CancellationException ?: CancellationException("$classSimpleName was cancelled", it)
        })
    }

    override fun handleJobException(exception: Throwable): Boolean {
        handleCoroutineException(context, exception)
        return true
    }
}
```

- `ProducerCoroutine`처럼 `ChannelCoroutine`을 상속해 `Job`이면서 채널입니다. 다만 돌려줄 때는 `SendChannel` 타입이라 바깥에서는 보내기만 할 수 있습니다.
- 블록의 수신 객체 `ActorScope<E>`는 `CoroutineScope`와 `ReceiveChannel<E>`를 함께 상속하고, 메일박스를 가리키는 `channel` 속성도 갖습니다. 그래서 블록 안에서 `for (message in channel)`이나 `receive()`로 메시지를 꺼냅니다. 보내는 쪽(`ProducerScope`)과 받는 쪽(`ActorScope`)이 서로 반대입니다.
- 액터가 취소되면 `onCancelling`에서 메일박스도 취소합니다. 이후 보내는 `send`는 실패하고, 메시지를 기다리던 `receive`는 `CancellationException`을 던집니다.
- `launch`와 같이 `handleJobException`을 정의하므로, 액터 안에서 잡히지 않은 예외는 `CoroutineExceptionHandler`로 보고됩니다.

`LAZY`로 만든 액터는 첫 메시지가 올 때 시작합니다.

```kotlin
// LazyActor.kt
@file:OptIn(ObsoleteCoroutinesApi::class)

import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*

fun main() = runBlocking<Unit> {
    val printer = actor<String>(start = CoroutineStart.LAZY) {
        println("액터 시작")
        for (message in channel) {
            println("받음: $message")
        }
    }

    delay(100)
    println("아직 메시지를 보내지 않음")

    printer.send("안녕")   // 첫 send 가 액터를 시작합니다
    printer.close()
}
```

```text
아직 메시지를 보내지 않음
액터 시작
받음: 안녕
```

`LazyActorCoroutine`은 `send`, `trySend`, `close` 같은 채널 쓰기 메서드를 고쳐 써서, 실제로 보내기 전에 `start()`를 먼저 부릅니다.

```kotlin
// LazyActorCoroutine (의사 코드, 실제 소스: kotlinx-coroutines 1.11.0 Actor.kt)
override suspend fun send(element: E) {
    start()                   // 처음이면 액터를 시작하고, 이미 시작했으면 아무 일도 하지 않습니다
    return super.send(element)
}
```

## 빌더 고르기 {#choosing}

| 하려는 일 | 빌더 | 받는 것 |
|---|---|---|
| 일을 시켜 두고 결과는 필요 없음 | `launch` | `Job` |
| 동시에 계산하고 결과를 모음 | `async` | `Deferred<T>`, `await()`로 결과 |
| 일반 함수(`main`, 테스트)에서 코루틴 실행을 끝까지 기다림 | `runBlocking` | 블록의 결과 |
| 값을 차례로 만들어 다른 코루틴에 흘려보냄 | `produce` | `ReceiveChannel<E>` |
| 상태 하나를 메시지로만 고치게 함 | `actor` | `SendChannel<E>` |

`produce`와 `actor`는 각각 실험 API, 낡을 예정인 API입니다. 값의 흐름은 요즘 `Flow`로, 공유 상태 보호는 `Mutex`나 `StateFlow`로 푸는 경우가 많습니다.

## 요약 {#summary}

코루틴 빌더는 일반 코드에서 코루틴을 만들고 시작하는 함수입니다. 모든 빌더는 같은 네 단계를 거칩니다. 부모 컨텍스트에 인자를 합쳐 새 컨텍스트를 만들고, 빌더마다 정해진 코루틴 클래스를 만들고, `start` 방식에 따라 실행을 시작하고, 만든 코루틴 객체를 그대로 핸들로 돌려줍니다. 코루틴 객체가 `Job`·`Deferred`·채널 인터페이스를 직접 구현하므로 따로 핸들을 만들 필요가 없습니다.

`launch`는 `Job`을, `async`는 결과를 담는 `Deferred<T>`를 돌려줍니다. `runBlocking`은 부른 스레드를 막고 블록의 결과를 돌려줍니다. `produce`는 코루틴이 끝나면 닫히는 `ReceiveChannel`을, `actor`는 메일박스로 쓰는 `SendChannel`을 돌려줍니다. 예외 보고 방식은 코루틴 클래스가 정합니다. `launch`와 `actor`는 `handleJobException`으로 예외를 보고하고, `async`는 `Deferred`에 보관했다가 `await()`에서 던집니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 코루틴 빌더들이 공통으로 거치는 단계는 무엇인가요?">

네 단계입니다. 먼저 `newCoroutineContext`로 부모 스코프의 컨텍스트와 인자로 받은 컨텍스트를 합칩니다. 같은 종류의 요소는 인자 쪽이 이기고, 디스패처가 하나도 없으면 `Dispatchers.Default`가 붙습니다.

다음으로 빌더마다 정해진 코루틴 클래스(`StandaloneCoroutine`, `DeferredCoroutine`, `ProducerCoroutine` 등)를 만들고, `start` 방식에 따라 실행을 시작합니다. 마지막으로 그 코루틴 객체를 그대로 돌려줍니다. 객체가 `Job`이나 `Deferred`, 채널 인터페이스를 직접 구현하기 때문입니다.

</def>
<def title="Q) launch 와 runBlocking 은 둘 다 코루틴을 만드는데 무엇이 다른가요?">

`launch`는 `CoroutineScope`의 확장 함수라 부모 스코프 안에서만 부를 수 있고, 코루틴을 시작한 뒤 바로 `Job`을 돌려줍니다. 부른 쪽은 기다리지 않고 다음 코드를 실행합니다.

`runBlocking`은 일반 함수라 어디서나 부를 수 있고, 코루틴과 자식이 모두 끝날 때까지 부른 스레드를 막습니다. 반환 값은 `Job`이 아니라 블록의 결과입니다. 스레드를 막기 때문에 `main` 함수나 테스트처럼 일반 코드와 코루틴을 잇는 곳에서만 씁니다.

</def>
<def title="Q) CoroutineStart.LAZY 로 만든 코루틴은 언제 시작되나요?">

`start()`, `join()`, 그리고 `async`라면 `await()`를 처음 부를 때 시작합니다. `LAZY`일 때 만드는 `LazyStandaloneCoroutine`, `LazyDeferredCoroutine`은 `active = false`로 생성되고, 생성자에서 블록의 첫 `Continuation`만 만들어 둡니다. `onStart`가 불릴 때 그것을 실행에 넘깁니다.

`LAZY` 액터는 첫 `send`가 시작시킵니다. `async`에 `LAZY`를 붙이고 `await()`를 차례로 부르면 하나가 끝나야 다음 것이 시작되어 동시에 실행되지 않으니 주의해야 합니다.

</def>
<def title="Q) produce 로 만든 채널은 언제 닫히나요?">

생산자 코루틴이 끝날 때 닫힙니다. `ProducerCoroutine`은 블록이 정상적으로 끝나면 `onCompleted`에서 채널을 닫고, 취소되거나 예외로 끝나면 `onCancelled`에서 그 원인을 담아 채널을 닫습니다.

그래서 받는 쪽의 `for` 문은 블록이 끝나면 자연스럽게 끝나고, 생산자가 예외로 끝났다면 받는 쪽에서 같은 예외가 던져집니다.

</def>
<def title="Q) actor 가 잠금 없이 공유 상태를 안전하게 다루는 원리는 무엇인가요?">

상태를 액터 코루틴 하나만 읽고 씁니다. 다른 코루틴은 상태에 직접 손대지 않고 메일박스 채널로 메시지만 보냅니다. 메시지가 여러 스레드에서 동시에 들어와도 액터가 하나씩 꺼내 차례로 처리하므로 경쟁 상태가 생기지 않습니다.

결과를 돌려받아야 하면 응답용 `CompletableDeferred`를 메시지에 담아 보내고 `await()`로 받습니다. 다만 `actor`는 `@ObsoleteCoroutinesApi`이고 JVM 전용입니다.

</def>
</deflist>
