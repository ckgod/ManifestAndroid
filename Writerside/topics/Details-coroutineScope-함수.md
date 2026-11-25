# Details: coroutineScope 함수

`coroutineScope { }`는 `suspend` 함수 안에서 임시 스코프를 하나 열어 주는 함수입니다. 블록 안에서는 `launch`, `async`로 여러 코루틴을 동시에 시작할 수 있고, 함수는 그 코루틴들이 **모두 끝난 뒤에** 돌아옵니다. `suspend` 함수 하나가 일을 여러 갈래로 나눠 동시에 처리하고, 다 모아서 결과를 돌려줄 때 씁니다.

[Q37](Q37-coroutine-scope.md#scope-object-vs-function)에서 스코프 객체와 이 함수의 차이를 봤습니다. 여기서는 이 함수가 지키는 규칙, 실패했을 때의 동작, 그리고 그것을 만드는 내부 구현(`ScopeCoroutine`)을 봅니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했고, 소스도 같은 버전에서 옮겼습니다.

## 네 가지 규칙 {#rules}

1. **컨텍스트를 이어받습니다.** 블록은 호출한 코루틴의 컨텍스트(디스패처, 이름 등)를 그대로 씁니다. 다만 `Job`만은 새로 만들어 호출한 코루틴의 자식으로 붙입니다.
2. **자식을 모두 기다립니다.** 블록의 마지막 줄까지 실행해도, 블록 안에서 시작한 코루틴이 남아 있으면 그것들이 끝날 때까지 돌아오지 않습니다.
3. **하나가 실패하면 모두 취소합니다.** 자식 하나가 예외로 실패하면 나머지 자식과 블록 자체를 취소합니다.
4. **실패를 예외로 던집니다.** 3번의 예외를 `coroutineScope`를 부른 곳에 그대로 다시 던집니다. 그래서 호출한 쪽에서 평범한 `try-catch`로 잡을 수 있습니다.

바깥에서 들어오는 취소도 받습니다. 호출한 코루틴이 취소되면 새 `Job`이 그 자식이므로 블록과 그 안의 코루틴이 모두 취소됩니다.

## 동시에 불러와 합치기 {#parallel-decomposition}

가장 흔한 쓰임은 여러 요청을 동시에 보내고 결과를 합치는 것입니다.

```kotlin
// ParallelLoad.kt
import kotlinx.coroutines.*

suspend fun loadProfile(): String {
    delay(1000)
    return "프로필"
}

suspend fun loadPosts(): String {
    delay(1000)
    return "게시글"
}

// 두 가지를 동시에 불러와 합칩니다
suspend fun loadScreen(): String = coroutineScope {
    val profile = async { loadProfile() }
    val posts = async { loadPosts() }
    "${profile.await()} + ${posts.await()}"
}

fun main() = runBlocking<Unit> {
    val start = System.currentTimeMillis()
    val screen = loadScreen()
    val seconds = (System.currentTimeMillis() - start) / 1000.0
    println("$screen, 약 ${"%.0f".format(seconds)}초")
}
```

```text
프로필 + 게시글, 약 1초
```

1초씩 걸리는 두 요청이 동시에 실행되어 합쳐서 약 1초가 걸렸습니다. `loadScreen`을 부르는 쪽에서 보면 그냥 결과를 돌려주는 `suspend` 함수입니다. 안에서 코루틴을 몇 개 시작했는지는 함수 밖으로 드러나지 않고, 함수가 돌아올 때는 안에서 시작한 코루틴이 하나도 남아 있지 않습니다.

`async`를 바깥 스코프(예를 들어 `viewModelScope`)에서 바로 부르지 않고 `coroutineScope`로 한 번 감싼 이유가 여기에 있습니다. 감싸지 않으면 두 `async`가 바깥 스코프의 자식이 되어 `loadScreen` 함수와 상관없이 바깥 스코프의 수명을 따릅니다. 함수가 돌아온 뒤에도 코루틴이 남을 수 있고, 하나가 실패했을 때 무슨 일이 생기는지도 바깥 스코프의 `Job` 종류에 따라 달라집니다. 일반 `Job`이면 바깥 스코프 전체가 취소되고, `SupervisorJob`이면 다른 요청이 쓸모없는 결과를 계속 불러옵니다.

책의 예제는 `async(Dispatchers.IO)`로 불러온 결과를 `withContext(Dispatchers.Main)` 안에서 화면에 표시합니다. `Dispatchers.Main`은 안드로이드 같은 플랫폼에서만 쓸 수 있어서 여기서는 디스패처를 빼고 같은 구조로 옮겼습니다.

## 하나가 실패하면 {#failure}

이번에는 프로필 요청이 실패하게 바꿨습니다.

```kotlin
// ScopeFailure.kt
import kotlinx.coroutines.*

suspend fun loadScreen(): String = coroutineScope {
    val profile = async {
        delay(100)
        throw IllegalStateException("프로필 서버 오류")
    }
    val posts = async {
        try {
            delay(1000)
            "게시글"
        } catch (e: CancellationException) {
            println("게시글 불러오기 취소됨")
            throw e
        }
    }
    "${profile.await()} + ${posts.await()}"
}

fun main() = runBlocking<Unit> {
    try {
        loadScreen()
    } catch (e: IllegalStateException) {
        // coroutineScope 가 자식의 예외를 그대로 다시 던집니다
        println("잡음: ${e.message}")
    }
    println("runBlocking 활성? $isActive")
}
```

```text
게시글 불러오기 취소됨
잡음: 프로필 서버 오류
runBlocking 활성? true
```

1. 프로필이 실패하자 `coroutineScope`의 `Job`이 취소되고, 아직 기다리던 게시글 요청도 취소됐습니다(규칙 3). 결과를 합칠 수 없으니 남은 요청을 기다릴 이유가 없습니다.
2. 실패 원인인 `IllegalStateException`이 `loadScreen()`을 부른 곳으로 던져져 `catch`에 잡혔습니다(규칙 4).
3. `runBlocking`은 취소되지 않았습니다. 예외가 `coroutineScope`에서 **부모를 취소하는 대신 호출한 곳에 예외로 던져졌기** 때문입니다. 호출한 쪽이 잡았으니 거기서 끝납니다.

3번이 `launch`를 바로 쓸 때와 가장 다른 점입니다.

```kotlin
// CatchLaunch.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    // 1. coroutineScope 로 감싸면 자식 launch 의 실패를 try-catch 로 잡을 수 있습니다
    try {
        coroutineScope {
            launch {
                delay(100)
                throw IllegalStateException("업로드 실패")
            }
            launch {
                delay(1000)
                println("다른 업로드 끝")   // 형제가 실패해 취소되므로 찍히지 않습니다
            }
        }
    } catch (e: IllegalStateException) {
        println("1) 잡음: ${e.message}")
    }

    // 2. coroutineScope 없이 launch 를 try 로 감싸면 잡히지 않습니다
    try {
        launch {
            delay(100)
            throw IllegalStateException("업로드 실패")
        }
    } catch (e: IllegalStateException) {
        println("2) 잡음: ${e.message}")
    }
    println("2) try 를 빠져나옴")
}
```

```text
1) 잡음: 업로드 실패
2) try 를 빠져나옴
Exception in thread "main" java.lang.IllegalStateException: 업로드 실패
	...
```

- 1)은 `coroutineScope`가 자식 `launch`의 실패를 모아 예외로 던졌으므로 `catch`에 잡혔습니다.
- 2)의 `launch`는 코루틴을 시작만 하고 바로 돌아오므로, 100ms 뒤의 예외는 이미 빠져나온 `try`와 상관이 없습니다. 예외는 부모인 `runBlocking`으로 올라가 `runBlocking`을 실패시켰고, `main`이 그 예외로 끝났습니다.

## 내부 구현 {#implementation}

```kotlin
// CoroutineScope.kt (kotlinx-coroutines 1.11.0)
public suspend fun <R> coroutineScope(block: suspend CoroutineScope.() -> R): R {
    contract {
        callsInPlace(block, InvocationKind.EXACTLY_ONCE)
    }
    return suspendCoroutineUninterceptedOrReturn { uCont ->
        val coroutine = ScopeCoroutine(uCont.context, uCont)
        coroutine.startUndispatchedOrReturn(coroutine, block)
    }
}
```

1. `suspendCoroutineUninterceptedOrReturn`은 지금 실행 중인 `suspend` 함수의 `Continuation`(`uCont`)을 꺼내 주는 저수준 함수입니다. Q32에서 본 대로 이 `Continuation`은 "`coroutineScope`가 끝난 뒤 이어서 실행할 나머지 코드"입니다.
2. `ScopeCoroutine(uCont.context, uCont)`로 임시 코루틴을 만듭니다. 컨텍스트로 호출한 코루틴의 것을 그대로 넘기므로, 그 안의 `Job`이 이 임시 코루틴의 부모가 됩니다(규칙 1). `uCont`는 나중에 호출한 쪽을 깨울 때 씁니다.
3. `startUndispatchedOrReturn`은 블록을 디스패처에 넘기지 않고 **지금 스레드에서 바로** 실행합니다. 이미 같은 컨텍스트에서 실행 중이므로 다른 스레드로 보낼 이유가 없습니다. 블록의 수신 객체(`this`)가 이 `ScopeCoroutine`이므로, 블록 안의 `launch`·`async`는 모두 `ScopeCoroutine`의 자식이 됩니다.

`contract { callsInPlace(..., EXACTLY_ONCE) }`는 "블록을 이 자리에서 정확히 한 번 실행한다"고 컴파일러에게 알려 줍니다. 그래서 블록 안에서 바깥의 `val` 변수를 초기화할 수 있습니다.

### 바로 돌아올지, 일시 중단할지 {#undispatched}

`startUndispatchedOrReturn`은 블록을 실행한 결과에 따라 세 갈래로 나뉩니다. 실제 코드(`Undispatched.kt`)를 이름을 붙여 옮긴 의사 코드입니다.

```kotlin
// (의사 코드) ScopeCoroutine.startUndispatchedOrReturn
fun startUndispatchedOrReturn(block): Any? {
    val blockResult = try {
        block.startHereWithoutDispatch(receiver = this)   // 첫 일시 중단 지점까지 바로 실행합니다
    } catch (e: Throwable) {
        Failed(e)
    }

    // 1. 블록이 중간에 일시 중단했습니다 → 나도 일시 중단합니다
    if (blockResult == SUSPENDED) return SUSPENDED

    // 2. 블록은 끝났지만 아직 실행 중인 자식이 있습니다 → 자식을 기다리며 일시 중단합니다
    val state = completeAndCheckChildren(blockResult)
    if (state == WAITING_FOR_CHILDREN) return SUSPENDED

    // 3. 블록도 자식도 다 끝났습니다 → 결과를 바로 돌려주거나 예외를 던집니다
    if (state is Failed) throw state.cause
    return state.value
}
```

3번 덕분에 블록이 한 번도 일시 중단하지 않고 끝나면(`coroutineScope { 42 }`) 일시 중단 없이 바로 값을 돌려줍니다. 1·2번처럼 일시 중단했다면 나중에 `ScopeCoroutine`이 완료될 때 호출한 쪽을 깨워야 하는데, 그 일은 완료 훅이 합니다.

### ScopeCoroutine {#scope-coroutine}

```kotlin
// Scopes.kt (kotlinx-coroutines 1.11.0, 디버그용 멤버 생략)
internal open class ScopeCoroutine<in T>(
    context: CoroutineContext,
    @JvmField val uCont: Continuation<T>   // 디스패처를 거치지 않은 원래 Continuation
) : AbstractCoroutine<T>(context, true, true) {

    final override val isScopedCoroutine: Boolean get() = true

    override fun afterCompletion(state: Any?) {
        // 다른 스레드에서 완료됐을 수 있으므로 디스패처를 거쳐 재개합니다
        uCont.intercepted().resumeCancellableWithInternal(recoverResult(state, uCont))
    }

    override fun afterResume(state: Any?) {
        // 이미 맞는 컨텍스트에 있으므로 바로 재개합니다
        uCont.resumeWith(recoverResult(state, uCont))
    }
}
```

`ScopeCoroutine`은 [AbstractCoroutine](Details-AbstractCoroutine의-내부-구조.md)을 상속하므로 `Job`이자 `CoroutineScope`이자 `Continuation`입니다. 여기서 볼 부분은 두 가지입니다.

**완료 훅에서 호출한 쪽을 깨웁니다(규칙 2).** `afterCompletion`은 `Job`이 최종 상태가 된 뒤에 불립니다. Q36에서 본 것처럼 `Job`은 자식이 모두 끝나야 최종 상태가 되므로, 이 훅이 불렸다면 블록과 자식이 모두 끝난 것입니다. 그때 `uCont`를 재개해서 `coroutineScope`를 부른 코드가 다음 줄로 넘어갑니다. `recoverResult`는 완료 상태에서 결과 값이나 예외를 꺼내, 정상이면 값으로 재개하고 실패면 예외로 재개합니다. 책의 인용에 있는 `resumeCancellableWith`는 1.11.0에서 `resumeCancellableWithInternal`로 이름이 바뀌었을 뿐 하는 일은 같습니다.

**`isScopedCoroutine = true`가 부모 취소를 막습니다(규칙 4).** 코루틴이 실패로 끝날 때 `JobSupport`는 부모에게 알릴지를 이 값으로 정합니다.

```kotlin
// JobSupport.kt (kotlinx-coroutines 1.11.0)
private fun cancelParent(cause: Throwable): Boolean {
    // Is scoped coroutine -- don't propagate, will be rethrown
    if (isScopedCoroutine) return true
    // ... 일반 코루틴은 여기서 부모의 childCancelled(cause) 를 부릅니다
}
```

일반 코루틴이라면 부모의 `childCancelled`를 불러 부모까지 취소합니다(Q36의 위로 가는 실패). `ScopeCoroutine`은 부모에게 알리지 않고 "처리했다"(`true`)고만 대답합니다. 주석 그대로, 이 예외는 `uCont`를 통해 호출한 곳에 다시 던져질 것이기 때문입니다. 앞의 `ScopeFailure.kt`에서 `runBlocking`이 취소되지 않은 이유가 이것입니다. 같은 이유로 `coroutineScope` 안의 실패는 `CoroutineExceptionHandler`로도 가지 않습니다.

## withContext와의 관계 {#with-context}

`withContext`도 같은 부품으로 만들어져 있습니다.

```kotlin
// Builders.common.kt (kotlinx-coroutines 1.11.0, 일부)
public suspend fun <T> withContext(context: CoroutineContext, block: suspend CoroutineScope.() -> T): T {
    return suspendCoroutineUninterceptedOrReturn sc@ { uCont ->
        val oldContext = uCont.context
        val newContext = oldContext.newCoroutineContext(context)
        newContext.ensureActive()
        // 1. 컨텍스트가 그대로면 coroutineScope 와 똑같이 ScopeCoroutine 을 씁니다
        if (newContext === oldContext) {
            val coroutine = ScopeCoroutine(newContext, uCont)
            return@sc coroutine.startUndispatchedOrReturn(coroutine, block)
        }
        // 2. 디스패처가 같으면 스레드를 옮기지 않고 바로 실행합니다
        // 3. 디스패처가 다르면 새 디스패처로 보내 실행합니다
        // ...
    }
}
```

1번 갈래가 `coroutineScope`의 구현과 같습니다. 즉 `coroutineScope { }`는 "컨텍스트를 바꾸지 않는 `withContext`"이고, `withContext(Dispatchers.IO) { }`는 "스레드를 바꾸는 `coroutineScope`"입니다. 둘 다 블록 안의 자식을 모두 기다리고, 실패를 예외로 다시 던지며, 호출한 코루틴의 자식으로 붙습니다.

## 쓰는 곳 {#when-to-use}

- **`suspend` 함수 안에서 일을 나눌 때.** 여러 요청을 `async`로 동시에 보내고 결과를 합치는 경우입니다. `suspend` 함수에는 `launch`를 부를 스코프가 없으므로, 스코프가 필요하면 `coroutineScope`로 엽니다.
- **함께 성공하거나 함께 실패해야 할 때.** 결과를 합쳐야 하는 작업처럼, 하나가 실패하면 나머지가 쓸모없는 경우에 맞습니다. 서로 독립적이라 하나가 실패해도 나머지를 살려야 한다면 [supervisorScope](Details-supervisorScope-함수.md)를 씁니다.
- **실패를 호출한 쪽에서 처리하고 싶을 때.** 자식 코루틴의 실패를 `try-catch` 하나로 받을 수 있습니다.

## 요약 {#summary}

`coroutineScope { }`는 호출한 코루틴의 컨텍스트를 이어받되 새 `Job`을 자식으로 붙인 임시 스코프에서 블록을 실행하고, 블록 안에서 시작한 코루틴이 모두 끝나야 돌아옵니다. 자식 하나가 실패하면 나머지를 모두 취소하고, 그 예외를 부모에게 올리지 않고 호출한 곳에 다시 던집니다.

내부에서는 `ScopeCoroutine`이 이 일을 합니다. 블록을 지금 스레드에서 바로 실행해 일시 중단이 없으면 값을 바로 돌려주고, 일시 중단했다면 자식까지 모두 끝난 뒤 `afterCompletion`에서 호출한 쪽의 `Continuation`을 재개합니다. `isScopedCoroutine`이 `true`라서 실패가 부모로 올라가지 않고 예외로 던져집니다. `withContext`도 컨텍스트가 같을 때는 같은 `ScopeCoroutine`을 씁니다.
