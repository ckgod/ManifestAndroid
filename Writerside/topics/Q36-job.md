# Q36) Job

`Job`은 코루틴 하나를 바깥에서 다루는 손잡이(핸들)입니다. 이 손잡이로 코루틴이 지금 실행 중인지, 끝났는지, 취소됐는지 확인하고, 취소를 요청하고, 끝날 때까지 기다립니다. 그리고 `Job`끼리 부모·자식으로 이어져서, 부모가 자식을 기다리고 부모를 취소하면 자식도 취소되는 구조화된 동시성(structured concurrency)을 만듭니다.

Q34에서 빌더가 만드는 코루틴 객체가 곧 `Job`이라는 것을 봤고, [AbstractCoroutine의 내부 구조](Details-AbstractCoroutine의-내부-구조.md)에서 상태를 담는 `_state` 필드와 부모 등록(`initParentJob`)을 봤습니다. 이 토픽에서는 `Job`을 쓰는 쪽에서 봅니다. 상태가 어떻게 바뀌는지, 취소가 실제로 언제 멈추는지, 취소와 실패가 부모·자식 사이에서 어느 방향으로 퍼지는지, 그리고 완료를 기다리고 알림 받는 방법입니다. 실패가 위로 퍼지지 않게 막는 `SupervisorJob`은 [SupervisorJob](Details-SupervisorJob.md)에서 따로 다룹니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했습니다. 라이브러리 내부 코드도 같은 버전의 소스에서 옮겼습니다.

## Job을 얻는 곳 {#getting-job}

`Job`은 세 군데에서 얻습니다.

| 얻는 곳 | 무엇이 나오나 |
|---|---|
| `launch { }`의 반환 값 | 방금 시작한 코루틴 (`async`는 `Job`을 상속한 `Deferred<T>`) |
| 코루틴 안에서 `currentCoroutineContext()[Job]` | 지금 실행 중인 코루틴 자신 |
| `Job()`, `SupervisorJob()` 함수 | 실행할 본문이 없는 `Job`. 스코프의 부모로 씁니다 |

`Job`은 코루틴 컨텍스트의 요소이기도 합니다.

```kotlin
// Job.kt (kotlinx-coroutines 1.11.0, 일부)
public interface Job : CoroutineContext.Element {
    public companion object Key : CoroutineContext.Key<Job>
    // ...
}
```

Q35에서 본 것처럼 요소 클래스의 `companion object`가 키입니다. 그래서 컨텍스트에서 `context[Job]`으로 꺼낼 수 있고, 빌더는 이어받은 컨텍스트에서 부모를 이렇게 찾습니다.

## 생명주기 상태 {#lifecycle}

`Job` 소스의 문서 주석에 있는 상태 전이도입니다.

```text
                                      wait children
+-----+ start  +--------+ complete   +-------------+  finish  +-----------+
| New | -----> | Active | ---------> | Completing  | -------> | Completed |
+-----+        +--------+            +-------------+          +-----------+
                 |  cancel / fail       |
                 |     +----------------+
                 |     |
                 V     V
             +------------+                           finish  +-----------+
             | Cancelling | --------------------------------> | Cancelled |
             +------------+                                   +-----------+
```

- **New**: `CoroutineStart.LAZY`로 만들어서 아직 시작하지 않은 상태입니다. 보통의 코루틴은 Active에서 시작합니다.
- **Active**: 실행 중이거나 실행을 기다리는 상태입니다.
- **Completing**: 본문은 끝났고 자식이 끝나기를 기다리는 상태입니다. 바깥에서 보면 Active와 구분되지 않습니다(`isActive`가 아직 `true`입니다).
- **Cancelling**: 취소됐거나 예외로 실패해서, 자식이 정리를 마치기를 기다리는 상태입니다.
- **Completed / Cancelled**: 자식까지 모두 끝난 최종 상태입니다.

바깥에서는 이 상태를 `isActive`, `isCompleted`, `isCancelled` 세 값으로 봅니다. 상태별 세 값의 표와, Completing·Cancelling을 실행으로 확인한 예제는 [AbstractCoroutine의 내부 구조](Details-AbstractCoroutine의-내부-구조.md#state-machine)에 있습니다.

`cancel()`을 부른 직후와 끝까지 기다린 뒤를 비교해 봤습니다.

```kotlin
// JobCancel.kt
import kotlinx.coroutines.*

fun Job.state(): String = "isActive=$isActive, isCompleted=$isCompleted, isCancelled=$isCancelled"

fun main() = runBlocking<Unit> {
    val job = launch {
        repeat(5) { i ->
            println("작업 $i 진행 중")
            delay(500L)
        }
    }

    delay(1300L)
    println("취소 요청")
    job.cancel()                       // 취소를 요청합니다
    println("cancel 직후: ${job.state()}")
    job.join()                         // 코루틴이 실제로 끝날 때까지 기다립니다
    println("join 이후:  ${job.state()}")
}
```

```text
작업 0 진행 중
작업 1 진행 중
작업 2 진행 중
취소 요청
cancel 직후: isActive=false, isCompleted=false, isCancelled=true
join 이후:  isActive=false, isCompleted=true, isCancelled=true
```

`cancel()` 직후에는 `isCancelled`가 `true`인데 `isCompleted`는 아직 `false`입니다. Cancelling 상태입니다. `cancel()`은 상태를 Cancelling으로 바꾸고 바로 돌아오는 함수이고, 코루틴이 실제로 멈추고 정리를 마치는 것은 그 뒤입니다. 그래서 취소한 뒤 정리가 끝난 것을 확인해야 하면 `join()`까지 부릅니다. 둘을 합친 `cancelAndJoin()`도 있습니다.

## 협력적 취소 {#cooperative-cancellation}

위 예제에서 코루틴이 멈춘 곳은 `delay`입니다. `cancel()`은 실행 중인 코드를 강제로 끊지 않습니다. 코루틴 쪽 코드가 취소됐는지 확인하는 지점에 도달해야 멈춥니다. `delay`, `yield`, `withContext` 같은 kotlinx-coroutines의 일시 중단 함수는 들어갈 때 취소 여부를 확인하고, 취소됐으면 `CancellationException`을 던집니다. 이 방식을 협력적 취소라고 부릅니다.

그래서 일시 중단 지점이 없는 코드는 취소해도 멈추지 않습니다.

```kotlin
// Cooperative.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    // 1. 일시 중단 지점이 없는 반복문은 취소해도 멈추지 않습니다
    val busy = launch(Dispatchers.Default) {
        var count = 0
        val until = System.currentTimeMillis() + 300
        while (System.currentTimeMillis() < until) {
            count++
        }
        println("1) 반복문이 끝까지 돌았습니다")
    }
    delay(50)
    busy.cancel()
    busy.join()

    // 2. isActive 를 확인하면 취소 요청을 보고 스스로 멈춥니다
    val polite = launch(Dispatchers.Default) {
        val until = System.currentTimeMillis() + 300
        while (System.currentTimeMillis() < until && isActive) {
            // 계산
        }
        println("2) isActive=$isActive 에서 멈췄습니다")
    }
    delay(50)
    polite.cancel()
    polite.join()
}
```

```text
1) 반복문이 끝까지 돌았습니다
2) isActive=false 에서 멈췄습니다
```

1)은 50ms에 취소했는데도 300ms짜리 반복문을 끝까지 돌았습니다. 오래 걸리는 계산 안에서는 2)처럼 `isActive`를 확인하거나, `ensureActive()`(취소됐으면 `CancellationException`을 던짐)나 `yield()`를 중간중간 불러야 취소가 먹힙니다.

## 부모와 자식 {#parent-child}

부모와 자식은 연결 손잡이(`ChildHandleNode`)로 이어집니다. 자식이 생성될 때 부모의 `attachChild`를 불러 이 손잡이를 부모의 리스너 목록에 넣습니다. 손잡이 클래스를 보면 신호가 양쪽으로 오가는 것이 보입니다.

```kotlin
// JobSupport.kt
private class ChildHandleNode(
    @JvmField val childJob: ChildJob
) : JobNode(), ChildHandle {
    override val parent: Job get() = job
    override val onCancelling: Boolean get() = true
    // 부모가 취소되기 시작하면 불립니다 → 자식을 취소합니다
    override fun invoke(cause: Throwable?) = childJob.parentCancelled(job)
    // 자식이 취소·실패하면 불립니다 → 부모에게 알립니다
    override fun childCancelled(cause: Throwable): Boolean = job.childCancelled(cause)
}
```

- **아래로 가는 취소.** `onCancelling`이 `true`라서 부모가 Cancelling이 되는 순간 `invoke`가 불리고, 자식의 `parentCancelled`가 자식을 취소합니다. 자식은 다시 자기 자식에게 같은 일을 하므로 취소가 맨 아래까지 내려갑니다.
- **위로 가는 실패.** 자식이 끝날 때 원인이 있으면 이 손잡이의 `childCancelled`로 부모에게 알립니다. 부모가 그 원인을 보고 자기도 취소할지 정합니다.

부모가 자식의 알림을 받았을 때 하는 일은 이렇습니다.

```kotlin
// JobSupport.kt
public open fun childCancelled(cause: Throwable): Boolean {
    if (cause is CancellationException) return true   // 1. 취소는 정상으로 봅니다
    return cancelImpl(cause) && handlesException       // 2. 그 밖의 예외면 자기도 취소합니다
}
```

1. 자식이 **취소**로 끝났으면(`CancellationException`) 부모는 아무것도 하지 않습니다. 부모가 자식 하나를 골라 취소하는 일은 흔하고 정상적인 흐름이기 때문입니다.
2. 자식이 **다른 예외로 실패**했으면 부모도 같은 원인으로 취소합니다(`cancelImpl`). 부모가 취소되면 아래로 가는 취소가 일어나서 나머지 자식(실패한 자식의 형제)도 모두 취소됩니다. 반환 값은 "이 예외를 위쪽에서 처리하겠다"는 뜻이고, 위쪽 어딘가에 예외를 맡을 코루틴이 있는지(`handlesException`)까지 따집니다. 책의 인용에는 `&& handlesException`이 빠져 있습니다.

먼저 취소 쪽입니다.

```kotlin
// ParentChild.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    // 1. 부모를 취소하면 자식도 취소됩니다
    val parent = launch {
        launch {
            try {
                delay(1000)
            } finally {
                println("1) 자식 A 취소됨")
            }
        }
        launch {
            try {
                delay(1000)
            } finally {
                println("1) 자식 B 취소됨")
            }
        }
    }
    delay(100)
    parent.cancel()
    parent.join()

    // 2. 자식 하나를 취소해도 부모와 형제는 그대로입니다
    val parent2 = launch {
        val child = launch { delay(1000) }
        launch {
            delay(200)
            println("2) 형제는 계속 실행됨")
        }
        delay(50)
        child.cancel()
    }
    parent2.join()
    println("2) 부모 취소됨? ${parent2.isCancelled}")
}
```

```text
1) 자식 A 취소됨
1) 자식 B 취소됨
2) 형제는 계속 실행됨
2) 부모 취소됨? false
```

다음은 실패 쪽입니다. 자식 A가 예외로 실패하면 부모를 거쳐 형제 B까지 취소됩니다.

```kotlin
// FailUp.kt
import kotlinx.coroutines.*

fun main() {
    val handler = CoroutineExceptionHandler { _, e -> println("핸들러: ${e.message}") }
    val scope = CoroutineScope(Job() + handler)

    val parent = scope.launch {
        launch {
            delay(100)
            throw IllegalStateException("자식 A 실패")
        }
        launch {
            try {
                delay(1000)
                println("자식 B 완료")
            } catch (e: CancellationException) {
                println("자식 B 취소됨")
                throw e
            }
        }
    }
    runBlocking { parent.join() }
    println("부모 취소됨? ${parent.isCancelled}")
    println("스코프의 Job 활성? ${scope.coroutineContext[Job]?.isActive}")
}
```

```text
자식 B 취소됨
핸들러: 자식 A 실패
부모 취소됨? true
스코프의 Job 활성? false
```

자식 A의 실패가 부모 `parent`를 취소했고, 부모의 취소가 자식 B를 취소했습니다. 실패는 거기서 멈추지 않고 스코프의 `Job()`까지 올라가서, 스코프도 더 이상 쓸 수 없게 되었습니다(`isActive=false`). 이 스코프에서 다시 `launch`를 해도 바로 취소됩니다. 한 곳의 실패가 같은 스코프 전체를 멈추는 것이 기본 동작이고, 이것을 막고 싶을 때 `SupervisorJob`을 씁니다.

자식 B에서 `CancellationException`을 잡은 뒤 다시 던진 부분도 봐 두어야 합니다. 이 예외를 삼키면 코루틴이 취소된 것을 모른 채 다음 코드를 계속 실행합니다.

## 부모 연결이 끊기는 경우 {#broken-parent}

Q35에서 빌더에 `Job`을 직접 넘기지 말라고 했습니다. 넘긴 `Job`이 새 코루틴의 부모가 되면서, 원래 부모와의 연결이 사라지기 때문입니다.

```kotlin
// BrokenParent.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val parent = launch {
        // 1. 평범한 자식
        launch {
            delay(300)
            println("1) 연결된 자식 끝")
        }
        // 2. Job() 을 넘긴 자식: 새 Job 이 부모가 되어 바깥 코루틴과 연결이 끊깁니다
        launch(Job()) {
            delay(300)
            println("2) 끊긴 자식 끝")
        }
    }
    delay(100)
    parent.cancel()
    parent.join()
    println("3) 부모 끝남")
    delay(500)
}
```

```text
3) 부모 끝남
2) 끊긴 자식 끝
```

- 1)은 부모가 취소될 때 함께 취소되어 아무것도 찍지 않았습니다.
- 2)는 부모가 취소되고 끝난 **뒤에도** 계속 실행되어 결과를 찍었습니다. 부모 `launch`는 이 코루틴을 자식으로 알지 못하므로 취소를 전하지도, 끝나기를 기다리지도 않습니다.

안드로이드라면 화면이 닫혀 `viewModelScope`가 취소된 뒤에도 작업이 계속 도는 누수가 됩니다. 디스패처나 이름을 바꾸려고 빌더에 컨텍스트를 넘기는 것은 괜찮지만, `Job`은 넘기지 않습니다.

## 완료 기다리기와 알림 {#join-completion}

코루틴이 끝나기를 기다리는 방법은 두 가지입니다.

- **`join()`**: `suspend` 함수입니다. 부른 코루틴을 일시 중단했다가 대상 `Job`이 최종 상태(Completed 또는 Cancelled)가 되면 재개합니다. 자식까지 다 끝나야 돌아옵니다.
- **`invokeOnCompletion { cause -> }`**: 일반 함수입니다. 최종 상태가 되면 불릴 콜백을 등록합니다. 콜백은 왜 끝났는지를 `cause`로 받습니다.

`join()`은 `invokeOnCompletion` 위에 만들어져 있습니다.

```kotlin
// JobSupport.kt
private suspend fun joinSuspend() = suspendCancellableCoroutine<Unit> { cont ->
    cont.disposeOnCancellation(invokeOnCompletion(handler = ResumeOnCompletion(cont)))
}

private class ResumeOnCompletion(
    private val continuation: Continuation<Unit>
) : JobNode() {
    override fun invoke(cause: Throwable?) = continuation.resume(Unit)
}
```

1. `suspendCancellableCoroutine`으로 지금 코루틴을 일시 중단하고 그 `Continuation`을 받습니다.
2. "끝나면 이 `Continuation`을 재개하라"는 리스너(`ResumeOnCompletion`)를 `invokeOnCompletion`으로 등록합니다.
3. 대상 `Job`이 끝나면 리스너가 `continuation.resume(Unit)`을 불러 기다리던 코루틴을 재개합니다.
4. `disposeOnCancellation`은 기다리던 쪽이 먼저 취소되면 등록한 리스너를 지워서, 끝난 뒤 쓸모없는 재개가 일어나지 않게 합니다.

`invokeOnCompletion`의 `cause`로는 끝난 이유를 구분할 수 있습니다.

```kotlin
// Completion.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    // 1. 정상 종료면 원인이 null 입니다
    val done = launch { delay(50) }
    done.invokeOnCompletion { cause -> println("1) 정상 종료, cause=$cause") }
    done.join()

    // 2. 취소면 CancellationException 이 옵니다
    val cancelled = launch { delay(1000) }
    cancelled.invokeOnCompletion { cause -> println("2) 취소, cause=${cause?.javaClass?.simpleName}") }
    delay(10)
    cancelled.cancel()
    cancelled.join()

    // 3. 예외로 끝나면 그 예외가 옵니다 (부모에 전파되지 않게 별도 스코프에서 실행)
    val scope = CoroutineScope(SupervisorJob() + CoroutineExceptionHandler { _, _ -> })
    val failed = scope.launch { throw IllegalStateException("실패") }
    failed.invokeOnCompletion { cause -> println("3) 실패, cause=$cause") }
    failed.join()
}
```

```text
1) 정상 종료, cause=null
2) 취소, cause=JobCancellationException
3) 실패, cause=java.lang.IllegalStateException: 실패
```

`JobCancellationException`은 `cancel()`이 만드는 `CancellationException`의 하위 클래스입니다. 콜백은 코루틴이 끝난 스레드에서 바로 불리고 일시 중단할 수 없으므로, 가볍고 빨리 끝나는 일(자원 해제, 로그)만 넣습니다.

## Job()과 CompletableJob {#completable-job}

`Job()` 함수는 실행할 본문이 없는 `Job`을 만듭니다. 반환 타입은 `Job`을 상속한 `CompletableJob`이고, 본문이 없으므로 "본문이 끝났다"는 신호를 `complete()`로 직접 줍니다.

```kotlin
// Job.kt
public fun Job(parent: Job? = null): CompletableJob = JobImpl(parent)
```

```kotlin
// CompletableJobEx.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val job = Job()                     // 본문 없는 Job. complete() 를 부를 때까지 활성입니다
    val scope = CoroutineScope(coroutineContext + job)

    scope.launch {
        delay(200)
        println("1) 자식 끝")
    }

    job.complete()                      // "더 받을 일은 없다"고 알립니다
    println("2) complete 직후 isActive=${job.isActive}, isCompleted=${job.isCompleted}")
    job.join()                          // 자식이 끝나야 완료됩니다
    println("3) join 이후 isCompleted=${job.isCompleted}")
}
```

```text
2) complete 직후 isActive=true, isCompleted=false
1) 자식 끝
3) join 이후 isCompleted=true
```

`complete()`는 `launch`의 본문이 끝난 것과 같은 일을 합니다. 그래서 자식이 남아 있으면 Completing 상태가 되어 `isActive`가 아직 `true`이고, 자식이 끝나야 Completed가 됩니다. 이렇게 `Job()`은 주로 스코프의 맨 위 부모로 쓰입니다. `CoroutineScope(context)`가 `Job`이 없을 때 붙여 주는 것도 이 `Job()`입니다.

`Job()`에 `parent`를 넘기면 그 `Job`의 자식으로 연결됩니다. 앞 절의 `launch(Job())`이 연결을 끊은 것은 `parent` 없이 만든 `Job()`, 즉 부모가 없는 새 뿌리를 넘겼기 때문입니다.

## 요약 {#summary}

`Job`은 코루틴의 상태를 보고, 취소하고, 기다리는 손잡이이자 컨텍스트 요소입니다. 상태는 New → Active → Completing → Completed로 가고, 취소나 실패가 있으면 Cancelling → Cancelled로 갑니다. Completing과 Cancelling은 자식을 기다리는 단계라서, 부모는 언제나 자식보다 늦게 끝납니다.

취소는 협력적입니다. `cancel()`은 상태만 바꾸고, 코드는 일시 중단 함수나 `isActive`·`ensureActive()` 확인 지점에 도달해야 멈춥니다. 정리까지 기다리려면 `join()`을 함께 부릅니다.

부모와 자식은 `ChildHandleNode`로 이어집니다. 부모가 취소되면 모든 자식이 취소되고, 자식 하나가 취소로 끝나는 것은 부모에게 영향이 없습니다. 자식이 다른 예외로 실패하면 부모가 취소되고, 그 결과 형제들도 모두 취소됩니다. 빌더에 `Job()`을 넘기면 이 연결이 끊겨 부모의 취소와 기다림이 닿지 않습니다.

완료는 `join()`으로 기다리거나 `invokeOnCompletion`으로 알림 받고, `join()`은 `invokeOnCompletion` 위에 만들어져 있습니다. `Job()`은 본문 없는 `CompletableJob`을 만들고 주로 스코프의 부모로 씁니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) cancel() 을 부른 직후 isCompleted 가 false 인 이유는 무엇인가요?">

`cancel()`은 상태를 Cancelling으로 바꾸고 바로 돌아오기 때문입니다. 코루틴은 다음 취소 확인 지점(예를 들어 `delay`)에서 `CancellationException`을 받아 멈추고, `finally` 블록 같은 정리 코드를 실행하고, 자식들도 모두 끝나야 Cancelled가 됩니다.

그래서 취소 직후에는 `isCancelled=true`, `isCompleted=false`입니다. 정리가 끝난 것까지 확인하려면 `join()`을 부르거나 `cancelAndJoin()`을 씁니다.

</def>
<def title="Q) 코루틴을 취소했는데 멈추지 않는 경우는 언제인가요?">

일시 중단 지점이 없이 계산만 하는 코드입니다. 취소는 협력적이라서, 코루틴 쪽 코드가 취소 여부를 확인하는 지점에 도달해야 멈춥니다. `delay`, `yield`, `withContext` 같은 일시 중단 함수가 그 지점입니다.

오래 걸리는 반복문 안에서는 `isActive`를 조건에 넣거나 `ensureActive()`, `yield()`를 중간중간 불러야 합니다. `CancellationException`을 `catch`로 잡고 다시 던지지 않는 경우도 취소가 무시됩니다.

</def>
<def title="Q) 자식 코루틴 하나가 취소된 것과 예외로 실패한 것은 부모에게 어떻게 다르게 전달되나요?">

자식이 끝나면 연결 손잡이로 부모의 `childCancelled(cause)`가 불립니다. 원인이 `CancellationException`이면 부모는 정상적인 일로 보고 아무것도 하지 않으므로 부모와 형제는 계속 실행됩니다.

원인이 다른 예외면 부모도 같은 원인으로 취소됩니다. 부모가 취소되면 다른 자식들에게 취소가 내려가서 형제들도 모두 취소되고, 실패는 부모의 부모로 계속 올라갑니다.

</def>
<def title="Q) launch(Job()) { } 처럼 Job 을 빌더에 넘기면 어떤 문제가 생기나요?">

넘긴 `Job()`이 새 코루틴의 부모가 되므로, 원래 그 `launch`를 부른 코루틴과의 부모·자식 연결이 없어집니다. 원래 부모는 이 코루틴을 자식으로 알지 못해서 취소될 때 함께 취소하지 않고, 끝날 때 기다리지도 않습니다.

결과적으로 부모 스코프가 취소된 뒤에도 작업이 계속 실행되는 누수가 생깁니다. 디스패처나 이름처럼 다른 요소는 빌더에 넘겨도 되지만 `Job`은 넘기지 않습니다.

</def>
<def title="Q) join() 은 내부적으로 어떻게 기다리나요?">

`suspendCancellableCoroutine`으로 지금 코루틴을 일시 중단하고, 그 `Continuation`을 재개하는 리스너(`ResumeOnCompletion`)를 대상 `Job`의 `invokeOnCompletion`으로 등록합니다. 대상이 최종 상태가 되면 리스너가 `resume(Unit)`을 불러 기다리던 코루틴을 깨웁니다.

기다리던 쪽이 먼저 취소되면 `disposeOnCancellation`이 리스너를 지웁니다. 스레드를 막고 기다리는 것이 아니라 일시 중단했다가 알림으로 재개하는 방식입니다.

</def>
</deflist>
