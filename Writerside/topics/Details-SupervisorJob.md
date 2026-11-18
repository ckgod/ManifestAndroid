# Details: SupervisorJob

[Q36](Q36-job.md#parent-child)에서 자식 하나가 예외로 실패하면 부모가 취소되고, 그 때문에 형제들까지 모두 취소되는 것을 봤습니다. 여러 작업이 하나의 결과를 함께 만드는 경우라면 맞는 동작입니다. 하나가 실패하면 나머지 결과도 쓸모가 없기 때문입니다. 하지만 화면 하나에서 프로필, 알림, 추천 목록을 따로따로 불러오는 경우라면, 추천 목록 하나가 실패했다고 나머지까지 멈출 이유가 없습니다.

`SupervisorJob`은 이런 경우를 위한 `Job`입니다. 부모가 취소되면 자식을 모두 취소하는 것은 같지만, **자식의 실패가 부모로 올라오지 않습니다.** 그래서 형제도 취소되지 않습니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했고, 소스도 같은 버전에서 옮겼습니다.

## Job과 비교 {#vs-job}

같은 코드를 부모만 바꿔서 실행해 봤습니다.

```kotlin
// SupervisorBook.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val supervisor = SupervisorJob()
    val scope = CoroutineScope(Dispatchers.Default + supervisor)

    val firstChild = scope.launch {
        println("첫째 시작")
        delay(1000L)
        throw RuntimeException("첫째 실패")
    }

    val secondChild = scope.launch {
        println("둘째 시작")
        try {
            delay(2000L)
            println("둘째 정상 완료")
        } catch (e: CancellationException) {
            println("둘째 취소됨")
            throw e
        }
    }

    firstChild.join()
    secondChild.join()
    println("끝, supervisor 활성? ${supervisor.isActive}")
}
```

`SupervisorJob()`일 때의 출력입니다(예외 스택 트레이스는 줄였습니다).

```text
첫째 시작
둘째 시작
Exception in thread "DefaultDispatcher-worker-1" java.lang.RuntimeException: 첫째 실패
	at SupervisorBookKt$main$1$firstChild$1.invokeSuspend(SupervisorBook.kt:10)
	...
둘째 정상 완료
끝, supervisor 활성? true
```

첫 줄의 `SupervisorJob()`을 `Job()`으로 바꾸면 이렇게 됩니다.

```text
첫째 시작
둘째 시작
둘째 취소됨
Exception in thread "DefaultDispatcher-worker-1" java.lang.RuntimeException: 첫째 실패
	...
끝, job 활성? false
```

| | `Job()` | `SupervisorJob()` |
|---|---|---|
| 첫째의 실패 | 부모로 올라감 | 첫째에서 끝남 |
| 둘째 | 취소됨 | 끝까지 실행됨 |
| 부모(스코프) | 취소되어 더 쓸 수 없음 | 활성 그대로, 계속 쓸 수 있음 |

두 경우 모두 예외 스택 트레이스가 찍혔습니다. 컨텍스트에 `CoroutineExceptionHandler`가 없어서 스레드의 기본 예외 처리기가 찍은 것입니다. 실패를 격리해도 예외 자체가 사라지지는 않습니다. 누가 그 예외를 처리하는지는 아래 [예외 처리 책임](#exception-handling)에서 봅니다.

## 한 줄짜리 구현 {#implementation}

`SupervisorJob`의 구현은 이것이 전부입니다.

```kotlin
// Supervisor.kt (kotlinx-coroutines 1.11.0)
public fun SupervisorJob(parent: Job? = null) : CompletableJob = SupervisorJobImpl(parent)

private class SupervisorJobImpl(parent: Job?) : JobImpl(parent) {
    override fun childCancelled(cause: Throwable): Boolean = false
}
```

`Job()`이 만드는 `JobImpl`을 상속하고, `childCancelled` 하나만 고쳐 썼습니다. Q36에서 본 원래 구현과 나란히 놓으면 차이가 분명합니다.

```kotlin
// JobSupport.kt — 일반 Job
public open fun childCancelled(cause: Throwable): Boolean {
    if (cause is CancellationException) return true
    return cancelImpl(cause) && handlesException   // 자식이 실패하면 나도 취소합니다
}

// Supervisor.kt — SupervisorJob
override fun childCancelled(cause: Throwable): Boolean = false   // 아무것도 하지 않습니다
```

`childCancelled`는 자식이 끝날 때 부모에게 원인을 알리는 함수입니다. 일반 `Job`은 원인이 실패면 `cancelImpl`로 자기를 취소하고, 그것이 형제 취소로 이어집니다. `SupervisorJobImpl`은 `cancelImpl`을 부르지 않으므로 자기도 형제도 취소되지 않습니다.

반환 값 `false`에도 뜻이 있습니다. `childCancelled`의 반환 값은 "이 예외를 내가(위쪽이) 처리하겠다"는 대답입니다. `false`는 "처리하지 않겠다"는 뜻이라서, 실패한 자식이 자기 예외를 스스로 처리해야 합니다.

아래로 가는 취소는 손대지 않았습니다. 부모가 취소될 때 자식을 취소하는 것은 `ChildHandleNode.invoke` 쪽 일이고 `SupervisorJobImpl`은 그 부분을 고쳐 쓰지 않았으므로, `SupervisorJob`을 취소하면 자식은 모두 취소됩니다.

## 예외 처리 책임 {#exception-handling}

일반 `Job` 아래에서는 실패가 맨 위 코루틴까지 올라가서 거기서 한 번 처리됩니다. `SupervisorJob` 아래에서는 실패가 위로 올라가지 않으므로, **`SupervisorJob`의 바로 아래 자식들이 각자 자기 예외를 처리합니다.** 이 자식들은 예외 처리에 관해서는 맨 위 코루틴처럼 행동합니다.

빌더에 따라 처리 방식이 다릅니다.

```kotlin
// SupervisorHandler.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val handler = CoroutineExceptionHandler { context, e ->
        println("핸들러: ${context[CoroutineName]?.name} -> ${e.message}")
    }
    val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default + handler)

    // launch: 실패한 자식이 스스로 핸들러에 보고합니다
    val a = scope.launch(CoroutineName("launch 자식")) {
        throw IllegalStateException("launch 실패")
    }

    // async: 예외를 보관했다가 await 에서 던집니다. 핸들러로는 가지 않습니다
    val b = scope.async(CoroutineName("async 자식")) {
        throw IllegalStateException("async 실패")
    }

    a.join()
    try {
        b.await()
    } catch (e: IllegalStateException) {
        println("await 에서 잡음: ${e.message}")
    }
}
```

```text
핸들러: launch 자식 -> launch 실패
await 에서 잡음: async 실패
```

- `launch`로 시작한 자식은 자기 컨텍스트의 `CoroutineExceptionHandler`에 보고합니다. 스코프에 넣어 둔 핸들러를 이어받았으므로 그것이 불렸습니다. 핸들러가 없으면 앞 절처럼 스레드의 기본 처리기로 가고, 안드로이드에서는 앱이 종료됩니다.
- `async`로 시작한 자식은 예외를 `Deferred`에 보관했다가 `await()`를 부른 쪽에 던집니다([launch와 async의 차이](Details-launch와-async의-차이.md)).

`SupervisorJob`을 쓰는 스코프에는 핸들러를 함께 넣거나, 각 자식 안에서 `try-catch`로 예외를 처리해 둡니다.

## supervisorScope {#supervisor-scope}

스코프 전체가 아니라 함수 하나 안에서만 실패를 격리하고 싶으면 `supervisorScope`를 씁니다. 블록 안에서 시작한 코루틴들의 부모가 `SupervisorJob`처럼 동작하는 임시 코루틴이 됩니다.

```kotlin
// Supervisor.kt (일부 생략)
public suspend fun <R> supervisorScope(block: suspend CoroutineScope.() -> R): R {
    return suspendCoroutineUninterceptedOrReturn { uCont ->
        val coroutine = SupervisorCoroutine(uCont.context, uCont)
        coroutine.startUndispatchedOrReturn(coroutine, block)
    }
}

private class SupervisorCoroutine<in T>(
    context: CoroutineContext,
    uCont: Continuation<T>
) : ScopeCoroutine<T>(context, uCont) {
    override fun childCancelled(cause: Throwable): Boolean = false
}
```

`SupervisorCoroutine`도 `childCancelled`를 `false`로 고쳐 쓴 것이 전부입니다. `coroutineScope`가 쓰는 `ScopeCoroutine`을 상속했으므로, 블록 안의 자식이 모두 끝날 때까지 기다렸다가 돌아오는 것은 `coroutineScope`와 같습니다.

```kotlin
// SupervisorScopeEx.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val handler = CoroutineExceptionHandler { _, e -> println("핸들러: ${e.message}") }

    // 같은 구조를 supervisorScope 로 감쌉니다
    val job = launch(handler) {
        supervisorScope {
            launch {
                delay(100)
                throw IllegalStateException("첫째 실패")
            }
            launch {
                delay(300)
                println("둘째 완료")
            }
        }
        println("supervisorScope 끝, 바깥 코루틴은 계속 실행")
    }
    job.join()
}
```

```text
핸들러: 첫째 실패
둘째 완료
supervisorScope 끝, 바깥 코루틴은 계속 실행
```

첫째의 실패는 `supervisorScope`에서 멈췄고, 둘째는 끝까지 실행됐으며, `supervisorScope`를 부른 바깥 코루틴도 계속 실행됐습니다. 실패한 첫째는 이어받은 핸들러에 스스로 보고했습니다. `supervisorScope` 블록 자체가 예외를 던지면 그것은 격리되지 않고 바깥으로 던져집니다. 격리되는 것은 블록 안에서 시작한 자식 코루틴의 실패입니다.

## 빌더 인자로 넘길 때의 함정 {#pitfall}

`SupervisorJob`을 빌더 인자로 넘기면 기대와 다르게 동작합니다.

```kotlin
// SupervisorPitfall.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val handler = CoroutineExceptionHandler { _, e -> println("핸들러: ${e.message}") }

    // SupervisorJob 을 빌더 인자로 넘겼습니다
    val job = launch(SupervisorJob() + handler) {
        // 이 두 코루틴의 부모는 SupervisorJob 이 아니라 바깥 launch 입니다
        launch {
            delay(100)
            throw IllegalStateException("첫째 실패")
        }
        launch {
            try {
                delay(1000)
                println("둘째 완료")
            } catch (e: CancellationException) {
                println("둘째 취소됨")
                throw e
            }
        }
    }
    job.join()
}
```

```text
둘째 취소됨
핸들러: 첫째 실패
```

`SupervisorJob`을 넣었는데도 둘째가 취소됐습니다. 이유는 Q36에서 본 부모 결정 방식에 있습니다.

1. `launch(SupervisorJob())`로 만든 코루틴은 그 자신이 새 `Job`(평범한 `StandaloneCoroutine`)이 되고, 넘긴 `SupervisorJob`은 그 코루틴의 **부모**가 됩니다.
2. 블록 안의 두 `launch`는 블록의 스코프, 즉 바깥 `launch` 코루틴을 부모로 삼습니다. 이 부모는 `SupervisorJob`이 아니라 일반 코루틴입니다.
3. 그래서 첫째의 실패는 일반 부모에게 올라가 부모를 취소하고, 부모가 둘째를 취소합니다. `SupervisorJob`은 한 단계 위에서 이 바깥 코루틴의 실패를 받아 줄 뿐입니다.

게다가 Q36의 [부모 연결이 끊기는 경우](Q36-job.md#broken-parent)처럼, 이 코드의 바깥 `launch`는 `runBlocking`과도 연결이 끊겨 있습니다. 자식끼리 실패를 격리하고 싶다면 그 자식들의 **바로 위 부모**가 `SupervisorJob`이어야 합니다. 스코프를 만들 때 넣거나(`CoroutineScope(SupervisorJob())`), `supervisorScope { }` 안에서 자식을 시작합니다.

## viewModelScope {#view-model-scope}

안드로이드의 `viewModelScope`가 대표적인 사용처입니다. 같은 화면에서 시작한 여러 작업 중 하나가 실패해도 나머지는 계속 실행되어야 하기 때문입니다. AndroidX Lifecycle 2.11.0 소스에서 스코프를 만드는 부분입니다.

```kotlin
// CloseableCoroutineScope.kt (androidx.lifecycle 2.11.0, 주석 줄임)
internal fun createViewModelScope(): CloseableCoroutineScope {
    val dispatcher =
        try {
            Dispatchers.Main.immediate
        } catch (_: NotImplementedError) {
            // Linux 같은 네이티브 환경처럼 Dispatchers.Main 이 없는 경우
            EmptyCoroutineContext
        } catch (_: IllegalStateException) {
            // 스윙 같은 JVM 데스크톱 환경처럼 Dispatchers.Main 이 없는 경우
            EmptyCoroutineContext
        }
    return CloseableCoroutineScope(coroutineContext = dispatcher + SupervisorJob())
}

internal class CloseableCoroutineScope(override val coroutineContext: CoroutineContext) :
    AutoCloseable, CoroutineScope {
    override fun close() = coroutineContext.cancel()
}
```

- 컨텍스트는 `Dispatchers.Main.immediate + SupervisorJob()`입니다. 그래서 `viewModelScope.launch { }`로 시작한 작업들은 서로의 실패에 영향을 받지 않습니다.
- `ViewModel`이 정리될 때 `onCleared()`보다 먼저 `close()`가 불리고, `SupervisorJob`을 취소해서 남은 작업을 모두 취소합니다. 아래로 가는 취소는 그대로라는 앞의 내용이 여기서 쓰입니다.
- 컨텍스트에 `CoroutineExceptionHandler`는 없습니다. 그래서 `viewModelScope.launch` 안의 잡히지 않은 예외는 스레드 기본 처리기로 가서 앱을 종료시킵니다. 실패를 격리해 준다는 것이 예외를 삼켜 준다는 뜻은 아니므로, 각 작업 안에서 예외를 처리해야 합니다.

`MainScope()`도 같은 구성(`SupervisorJob() + Dispatchers.Main`)입니다.

## 요약 {#summary}

`SupervisorJob`은 자식의 실패가 부모로 올라가지 않는 `Job`입니다. 구현은 `JobImpl`을 상속해 `childCancelled`가 항상 `false`를 돌려주게 고친 한 줄입니다. 부모가 자기를 취소하지 않으므로 형제도 취소되지 않고, `false`라는 대답 때문에 실패한 자식이 자기 예외를 스스로 처리합니다. `launch` 자식은 컨텍스트의 `CoroutineExceptionHandler`에 보고하고, `async` 자식은 `await()`에서 던집니다. 부모가 취소되면 자식을 모두 취소하는 것은 일반 `Job`과 같습니다.

함수 안에서만 격리하려면 같은 방식으로 만든 `supervisorScope`를 씁니다. 격리는 바로 아래 자식에게만 적용되므로, `launch(SupervisorJob()) { }`처럼 빌더 인자로 넘기면 블록 안의 자식들은 일반 부모 아래에 놓여 격리되지 않습니다. `viewModelScope`와 `MainScope()`는 `SupervisorJob`으로 만든 스코프이고, 예외 핸들러는 들어 있지 않습니다.
