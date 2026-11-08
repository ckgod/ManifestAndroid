# Details: launch와 async의 차이

`launch`와 `async`는 둘 다 부른 스레드를 막지 않고 새 코루틴을 시작합니다. 차이는 결과를 돌려주는지와 실패를 어떻게 알리는지에 있습니다. `launch`는 일을 시켜 두기만 하는 용도이고, `async`는 값을 계산해 나중에 받는 용도입니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했습니다.

## 반환 값과 쓰임 {#return-value}

`launch`는 `Job`을 돌려줍니다. `Job`으로 상태를 확인하고(`isActive`, `isCompleted`), 끝날 때까지 기다리고(`join()`), 취소할 수(`cancel()`) 있지만 결과 값은 받을 수 없습니다. 블록 타입이 `suspend CoroutineScope.() -> Unit`이라 블록 마지막 줄에 값이 있어도 버려집니다. "결과를 위한 것이 아니다"는 말은 블록이 값을 못 만든다는 뜻이 아니라, 만든 값을 부른 쪽에 전달하지 않는다는 뜻입니다.

```kotlin
// UpdateProfile.kt (안드로이드 ViewModel 예시)
fun updateUserProfile(name: String) {
    viewModelScope.launch {
        // 목적은 DB 에 쓰는 것 자체이고, 부른 쪽은 결과를 기다리지 않습니다
        userDao.update(name)
    }
    // 함수는 바로 돌아오고, launch 블록은 따로 실행됩니다
}
```

`async`는 `Deferred<T>`를 돌려줍니다. `Deferred`는 나중에 채워질 결과 하나를 담는 `Job`입니다. 다른 언어의 future(나중에 나올 결과를 읽는 자리)나 promise(나중에 결과를 채우는 객체)와 같은 개념입니다. 결과는 `suspend` 함수인 `await()`로 받습니다.

```kotlin
// LoadProfile.kt (안드로이드 ViewModel 예시)
fun loadUserProfile() {
    viewModelScope.launch {
        // 두 요청을 동시에 시작합니다
        val user: Deferred<User> = async { api.fetchUser() }
        val permissions: Deferred<List<Permission>> = async { api.fetchPermissions() }

        // await 는 결과가 나올 때까지 이 코루틴만 일시 중단합니다
        displayProfile(user.await(), permissions.await())
    }
}
```

두 요청이 동시에 진행되므로 전체 시간은 둘을 더한 값이 아니라 오래 걸리는 쪽에 맞춰집니다. 책은 이 예제를 `suspend fun` 안에서 `viewModelScope.async`로 썼는데, 그러면 두 코루틴이 그 함수가 아니라 ViewModel 스코프의 자식이 됩니다. 함수를 부른 쪽이 취소돼도 요청은 계속 돌게 되므로, 위처럼 한 코루틴 안에서 `async`를 부르거나 `suspend` 함수라면 `coroutineScope { }` 안에서 부르는 편이 맞습니다.

## 실패 전파 {#failure-propagation}

`async`의 예외는 `await()`를 부를 때까지 미뤄지니 그동안 부모와 형제는 멀쩡하다고 생각하기 쉽습니다. 그렇지 않습니다. 부모가 일반 `Job`이면 `async`가 실패하는 즉시 부모가 취소되고, 부모는 다른 자식도 모두 취소합니다.

```kotlin
// FailUnderJob.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val scope = CoroutineScope(Job())   // 일반 Job: 자식 하나가 실패하면 전부 취소됩니다

    val sibling = scope.launch {
        delay(500)
        println("형제 코루틴 완료")   // 출력되지 않습니다
    }
    val deferred = scope.async<String> {
        delay(10)
        throw IllegalStateException("async 실패")
    }

    delay(100)   // await 를 부르기 전입니다
    val scopeJob = scope.coroutineContext[Job]!!
    println("await 전: 스코프 isActive=${scopeJob.isActive}, 형제 isCancelled=${sibling.isCancelled}")

    try {
        deferred.await()
    } catch (e: IllegalStateException) {
        println("await 에서 받은 예외: ${e.message}")
    }
}
```

```text
await 전: 스코프 isActive=false, 형제 isCancelled=true
await 에서 받은 예외: async 실패
```

`await()`를 부르기 전인데 스코프는 이미 비활성 상태이고 형제 코루틴은 취소되었습니다. 예외 자체는 `await()`에서 다시 던져지지만, 실패가 부모에게 알려지는 시점은 `launch`와 같습니다. 책은 "`async`는 `await()`가 호출될 때까지 스코프를 크래시시키지 않으며, 다른 병렬 태스크는 완료될 수 있다"고 설명하는데, 형제가 살아남는 것은 아래처럼 부모가 `SupervisorJob`일 때뿐입니다.

`coroutineScope { }` 안에서도 마찬가지입니다. 그 안의 `async` 하나가 실패하면 `await()`를 부르지 않았어도 `coroutineScope` 전체가 취소되고 그 예외를 던집니다.

## 실패 보고 {#failure-reporting}

차이는 예외를 맡아 줄 부모 코루틴이 없을 때 드러납니다. `CoroutineScope(...)`로 직접 만든 스코프 바로 아래이거나 부모가 `SupervisorJob`이면, 코루틴이 자기 예외를 직접 처리해야 합니다. 이때 `launch`는 예외를 바로 보고하고, `async`는 `Deferred`에 넣어 둡니다.

```kotlin
// FailUnderSupervisor.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val handler = CoroutineExceptionHandler { _, e ->
        println("핸들러가 받은 예외: ${e.message}")
    }
    // SupervisorJob: 자식이 실패해도 스코프와 다른 자식은 그대로 둡니다
    val scope = CoroutineScope(SupervisorJob() + handler)

    val sibling = scope.launch {
        delay(300)
        println("형제 코루틴 완료")
    }

    // launch 의 예외는 그 자리에서 핸들러로 보고됩니다
    scope.launch { throw IllegalStateException("launch 실패") }

    // async 의 예외는 Deferred 안에 보관되고, 핸들러로 가지 않습니다
    val deferred = scope.async<String> { throw IllegalStateException("async 실패") }

    delay(100)
    println("await 전: 형제 isCancelled=${sibling.isCancelled}")
    try {
        deferred.await()
    } catch (e: IllegalStateException) {
        println("await 에서 받은 예외: ${e.message}")
    }
    sibling.join()
}
```

```text
핸들러가 받은 예외: launch 실패
await 전: 형제 isCancelled=false
await 에서 받은 예외: async 실패
형제 코루틴 완료
```

`launch`의 예외는 실패하자마자 `CoroutineExceptionHandler`로 갔습니다. 핸들러가 없었다면 스레드의 기본 예외 처리기로 가고, 안드로이드라면 앱이 종료됩니다. `async`의 예외는 핸들러로 가지 않고 `await()`에서 던져졌습니다. 반대로 말하면, 이런 `async`의 `await()`를 끝내 부르지 않으면 예외는 아무에게도 알려지지 않고 사라집니다.

이 차이는 코루틴 클래스 한 곳에서 나옵니다. 코루틴이 예외로 끝나면 `JobSupport`는 이렇게 처리합니다.

```kotlin
// JobSupport.finalizeFinishingState 일부 (kotlinx-coroutines 1.11.0)
val handled = cancelParent(finalException) || handleJobException(finalException)
```

먼저 `cancelParent`로 부모에게 알립니다. 부모가 일반 `Job`이면 이 호출에서 부모가 취소되고, 부모는 다른 자식도 취소합니다. 앞 절에서 형제가 취소된 것이 이 단계입니다. 그다음 부모가 예외 처리까지 이어받으면 `true`, 아니면 `false`를 돌려줍니다. 부모가 다른 코루틴(`launch`, `async`, `runBlocking` 등으로 만든 것)이면 그 코루틴이 예외를 위로 올려 보내므로 `true`입니다. `CoroutineScope(Job())`의 `Job`처럼 위에 코루틴이 없는 `Job`이거나 `SupervisorJob`이면 `false`가 나와 자기 `handleJobException`이 불립니다.

`launch`의 `StandaloneCoroutine`은 이 함수를 고쳐 써서 예외를 핸들러에 보고하고, `async`의 `DeferredCoroutine`은 고쳐 쓰지 않아 기본 구현(아무것도 하지 않음)이 쓰입니다. 예외는 코루틴의 최종 상태로 남아 있다가 `await()`가 꺼내 던집니다. 앞 절의 `FailUnderJob.kt`도 같은 경로를 탔습니다. 실패한 쪽이 `async`라 보고 없이 스코프만 취소되었고, `launch`였다면 스코프가 취소되면서 예외도 스레드 기본 처리기로 보고되었을 것입니다.

같은 이유로 `CoroutineExceptionHandler`는 스코프에 넣거나 스코프 바로 아래의 `launch`에 붙여야 효과가 있습니다. 다른 코루틴 안에서 시작한 자식 `launch`에 붙이면 예외가 부모 코루틴으로 넘어가 버려 그 핸들러는 쓰이지 않습니다.

## 비교표 {#comparison}

| | `launch` | `async` |
|---|---|---|
| 용도 | 일을 시켜 두기 (결과 불필요) | 값을 계산해 나중에 받기 |
| 반환 | `Job` | `Deferred<T>` (`Job`을 상속) |
| 결과 받기 | 불가능 | `await()` |
| 일반 `Job` 아래에서 실패 | 즉시 부모·형제 취소 | 즉시 부모·형제 취소 (같음) |
| 예외를 맡을 부모 코루틴이 없을 때 | `CoroutineExceptionHandler`, 없으면 스레드 기본 처리기로 보고 | `Deferred`에 보관, `await()`에서 던짐 |
| 대표 사례 | 화면 갱신, DB 저장, 동기화 시작 | 여러 네트워크 요청을 동시에 보내고 결과 합치기 |

결과가 필요하면 `async`, 필요 없으면 `launch`입니다. 결과가 필요 없는데 `async`를 쓰면 `await()`를 부르지 않는 순간 예외가 조용히 사라질 수 있으니 피합니다.

## 요약 {#summary}

`launch`는 `Job`을 돌려주고 블록의 값은 버립니다. `async`는 결과를 담는 `Deferred<T>`를 돌려주고 `await()`로 그 값을 받습니다. 실패는 둘 다 즉시 부모에게 알리므로, 일반 `Job` 아래에서는 어느 쪽이 실패해도 부모와 형제가 함께 취소됩니다. 예외를 맡아 줄 부모 코루틴이 없는 경우(직접 만든 스코프 바로 아래, `SupervisorJob`)에만 차이가 나서, `launch`는 예외 처리기로 바로 보고하고 `async`는 `Deferred`에 보관했다가 `await()`에서 던집니다.
