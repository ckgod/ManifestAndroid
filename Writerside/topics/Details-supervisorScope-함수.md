# Details: supervisorScope 함수

`supervisorScope { }`는 [coroutineScope](Details-coroutineScope-함수.md)와 거의 같은 함수입니다. 임시 스코프를 열어 블록을 실행하고, 블록 안에서 시작한 코루틴이 모두 끝나야 돌아옵니다. 다른 점은 하나입니다. **자식 하나가 실패해도 다른 자식을 취소하지 않습니다.** 서로 독립적인 작업 여러 개를 동시에 돌리면서, 일부가 실패해도 나머지 결과는 살리고 싶을 때 씁니다.

구현이 `SupervisorJob`과 같은 원리라서 [SupervisorJob](Details-SupervisorJob.md#supervisor-scope)에서 한 번 짧게 다뤘습니다. 이 토픽에서는 `coroutineScope`와 나란히 놓고 차이를 확인하고, 실패한 자식의 예외가 어디로 가는지, 격리가 어디까지 적용되는지, 비슷해 보이지만 다르게 동작하는 코드를 봅니다.

예제는 Kotlin 2.4.21, kotlinx-coroutines 1.11.0, JDK 25에서 실행했고, 소스도 같은 버전에서 옮겼습니다.

## coroutineScope와 비교 {#vs-coroutine-scope}

같은 두 자식을 `coroutineScope`와 `supervisorScope`로 각각 감싸 실행했습니다. 첫째는 100ms 뒤에 실패하고, 둘째는 300ms 뒤에 끝납니다.

```kotlin
// ScopeCompare.kt
import kotlinx.coroutines.*

// 첫째는 실패하고 둘째는 300ms 뒤에 끝나는 두 자식을 시작합니다
fun CoroutineScope.startTwoChildren(label: String) {
    launch {
        delay(100)
        throw IllegalStateException("첫째 실패")
    }
    launch {
        try {
            delay(300)
            println("$label 둘째 완료")
        } catch (e: CancellationException) {
            println("$label 둘째 취소됨")
            throw e
        }
    }
}

fun main() = runBlocking<Unit> {
    val handler = CoroutineExceptionHandler { _, e -> println("핸들러: ${e.message}") }

    withContext(handler) {
        // 1. coroutineScope
        try {
            coroutineScope { startTwoChildren("1)") }
            println("1) 정상 반환")
        } catch (e: IllegalStateException) {
            println("1) 예외를 다시 던짐: ${e.message}")
        }

        // 2. supervisorScope
        try {
            supervisorScope { startTwoChildren("2)") }
            println("2) 정상 반환")
        } catch (e: IllegalStateException) {
            println("2) 예외를 다시 던짐: ${e.message}")
        }
    }
}
```

```text
1) 둘째 취소됨
1) 예외를 다시 던짐: 첫째 실패
핸들러: 첫째 실패
2) 둘째 완료
2) 정상 반환
```

| | `coroutineScope` | `supervisorScope` |
|---|---|---|
| 형제(둘째) | 취소됨 | 끝까지 실행됨 |
| 함수의 결과 | 첫째의 예외를 다시 던짐 | 정상 반환 |
| 첫째의 예외 | 호출한 곳의 `catch`로 감 | `CoroutineExceptionHandler`로 감 |
| 자식을 모두 기다림 | 예 | 예 |

마지막 줄이 두 함수의 공통점입니다. 둘 다 구조화된 동시성을 지킵니다. 갈리는 것은 실패를 다루는 방식뿐입니다. `coroutineScope`는 실패를 "함수 전체의 실패"로 보고 호출한 곳에 던집니다. `supervisorScope`는 "그 자식 하나의 실패"로 보고 자식에게 맡깁니다.

책의 예제는 첫째 자식이 `try-catch`로 자기 예외를 직접 잡습니다. 그러면 첫째는 실패가 아니라 정상 완료로 끝나므로, `supervisorScope`를 `coroutineScope`로 바꿔도 출력이 똑같습니다. 두 함수의 차이를 보려면 위처럼 예외가 자식 밖으로 나가게 해야 합니다.

## 구현 {#implementation}

```kotlin
// Supervisor.kt (kotlinx-coroutines 1.11.0, contract 생략)
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

`coroutineScope`의 구현에서 `ScopeCoroutine`을 `SupervisorCoroutine`으로 바꾼 것이 전부입니다. `SupervisorCoroutine`은 `ScopeCoroutine`을 상속해서 두 성질을 함께 가집니다.

- **`ScopeCoroutine`에서 물려받은 것.** 블록을 지금 스레드에서 바로 실행하고, 자식이 모두 끝나면 `afterCompletion`에서 호출한 쪽을 재개합니다. `isScopedCoroutine = true`라서 **자기 자신의 실패**는 부모에게 올리지 않고 호출한 곳에 예외로 던집니다.
- **새로 고친 것.** `childCancelled`가 항상 `false`를 돌려줍니다. 자식이 실패했다는 알림을 받아도 자기를 취소하지 않으므로 다른 자식도 취소되지 않습니다. `false`는 "이 예외를 내가 처리하지 않겠다"는 대답이기도 해서, 실패한 자식이 자기 예외를 스스로 처리하게 됩니다([SupervisorJob의 한 줄짜리 구현](Details-SupervisorJob.md#implementation)).

앞 예제에서 첫째의 예외가 핸들러로 간 것은 이 두 번째 성질 때문입니다. 첫째는 예외를 맡아 줄 부모가 없다는 대답을 받았으므로, 맨 위 코루틴처럼 자기 컨텍스트의 `CoroutineExceptionHandler`에 보고했습니다. 핸들러는 `withContext(handler)`에서 이어받은 것입니다. 핸들러가 없었다면 스레드의 기본 예외 처리기로 가서 JVM에서는 스택 트레이스가 찍히고, 안드로이드에서는 앱이 종료됩니다.

## 일부 결과만 살리기 {#partial-results}

`async`로 시작한 자식은 핸들러로 보고하지 않고 예외를 `Deferred`에 담아 둡니다([launch와 async의 차이](Details-launch와-async의-차이.md)). 그래서 `supervisorScope`와 `async`를 함께 쓰면 "성공한 것만 모으기"를 깔끔하게 만들 수 있습니다.

```kotlin
// PartialResults.kt
import kotlinx.coroutines.*
import java.io.IOException

suspend fun loadWidget(name: String): String {
    delay(100)
    if (name == "날씨") throw IOException("날씨 서버 오류")
    return "$name 위젯"
}

// 불러온 위젯만 모아서 돌려줍니다. 하나가 실패해도 나머지는 살립니다
suspend fun loadWidgets(names: List<String>): List<String> = supervisorScope {
    val requests = names.map { name -> async { loadWidget(name) } }
    val loaded = mutableListOf<String>()
    for (request in requests) {
        try {
            loaded += request.await()
        } catch (e: IOException) {
            println("건너뜀: ${e.message}")
        }
    }
    loaded
}

fun main() = runBlocking<Unit> {
    println(loadWidgets(listOf("일정", "날씨", "뉴스")))
}
```

```text
건너뜀: 날씨 서버 오류
[일정 위젯, 뉴스 위젯]
```

세 요청이 동시에 나갔고, 날씨만 실패했습니다. 실패한 `async`는 형제를 취소하지 않았고, 예외는 `await()`에서 던져져 그 자리에서 처리됐습니다. 같은 코드를 `coroutineScope`로 감싸면 날씨가 실패하는 순간 일정·뉴스 요청도 취소되고 `loadWidgets` 전체가 예외로 끝납니다.

`catch`에 `IOException`처럼 구체적인 예외 타입을 적은 데도 이유가 있습니다. 코루틴의 `CancellationException`은 자바의 `IllegalStateException`을 상속합니다. 그래서 `catch (e: IllegalStateException)`이나 `catch (e: Exception)`으로 `await()`를 감싸면, 바깥에서 취소되어 `await()`가 던진 `CancellationException`까지 잡혀서 취소를 무시하고 다음 줄로 진행해 버립니다. `coroutineScope`로 바꿔 `IllegalStateException`을 잡게 해 보면, 날씨가 실패한 뒤 취소된 나머지 요청의 `await()`도 "건너뜀"으로 찍힙니다.

## 블록 자체가 실패할 때 {#block-failure}

격리되는 것은 블록 안에서 **시작한 자식 코루틴**의 실패입니다. 블록 본문이 직접 예외를 던지면 `coroutineScope`와 똑같이 동작합니다.

```kotlin
// SupervisorEdge.kt (1번)
try {
    supervisorScope {
        launch {
            try {
                delay(1000)
            } finally {
                println("1) 자식 취소됨")
            }
        }
        delay(100)
        throw IllegalStateException("블록 실패")
    }
} catch (e: IllegalStateException) {
    println("1) 잡음: ${e.message}")
}
```

```text
1) 자식 취소됨
1) 잡음: 블록 실패
```

블록이 실패하면 `SupervisorCoroutine` 자신이 실패한 것이므로 자식을 모두 취소하고, `ScopeCoroutine`에서 물려받은 대로 예외를 호출한 곳에 던집니다. 앞 예제의 `loadWidgets`에서 `await()`를 `try-catch`로 감싼 이유도 이것입니다. `await()`가 던진 예외를 블록 안에서 잡지 않으면 블록이 실패하고, 남은 요청까지 모두 취소됩니다.

## 격리는 바로 아래 자식까지 {#direct-children-only}

`supervisorScope`의 규칙은 **바로 아래 자식**에게만 적용됩니다. 그 자식이 다시 시작한 손자들의 부모는 평범한 코루틴입니다.

```kotlin
// SupervisorEdge.kt (2번)
val handler = CoroutineExceptionHandler { _, e -> println("핸들러: ${e.message}") }

supervisorScope {
    launch(handler) {
        // 자식 A 안에서 시작한 손자 둘은 A 가 일반 부모라서 함께 취소됩니다
        launch {
            delay(100)
            throw IllegalStateException("손자 실패")
        }
        launch {
            try {
                delay(300)
            } finally {
                println("2) 손자 형제 취소됨")
            }
        }
    }
    launch {
        delay(300)
        println("2) 자식 B 완료")   // A 의 실패와 무관합니다
    }
}
```

```text
2) 손자 형제 취소됨
핸들러: 손자 실패
2) 자식 B 완료
```

1. 손자의 실패는 일반 코루틴인 자식 A로 올라가 A를 취소했고, A가 다른 손자를 취소했습니다. 이 단계는 Q36에서 본 기본 동작 그대로입니다.
2. A의 실패가 `supervisorScope`에 도착하자 거기서 멈췄습니다. 자식 B는 영향 없이 끝났습니다.
3. A가 맨 위 코루틴처럼 예외를 처리하므로 A의 컨텍스트에 넣은 `handler`가 불렸습니다.

손자들끼리도 격리하고 싶다면 A 안에서 다시 `supervisorScope { }`를 엽니다.

## 비슷해 보이는 다른 코드 {#look-alikes}

`supervisorScope { }` 대신 `SupervisorJob`을 컨텍스트로 넘기는 코드를 쓰기 쉽습니다. 모양은 비슷하지만 격리가 되지 않습니다.

```kotlin
// WithContextSupervisor.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    try {
        // supervisorScope 대신 withContext(SupervisorJob()) 을 썼습니다
        withContext(SupervisorJob()) {
            launch {
                delay(100)
                throw IllegalStateException("첫째 실패")
            }
            launch {
                try {
                    delay(300)
                    println("둘째 완료")
                } catch (e: CancellationException) {
                    println("둘째 취소됨")
                    throw e
                }
            }
        }
    } catch (e: IllegalStateException) {
        println("잡음: ${e.message}")
    }
}
```

```text
둘째 취소됨
잡음: 첫째 실패
```

`withContext`는 넘긴 `SupervisorJob`을 블록의 `Job`으로 쓰지 않습니다. 새 코루틴(일반 코루틴)을 만들고 넘긴 `SupervisorJob`을 그 **부모**로 삼습니다. 블록 안의 두 `launch`는 이 일반 코루틴의 자식이므로 첫째의 실패가 둘째를 취소했습니다. [빌더 인자로 넘길 때의 함정](Details-SupervisorJob.md#pitfall)에서 본 `launch(SupervisorJob())`과 같은 구조입니다. 게다가 블록의 부모가 바깥 코루틴이 아니라 새 `SupervisorJob`이 되었으므로, Q36의 [부모 연결이 끊기는 경우](Q36-job.md#broken-parent)와 같은 문제도 함께 생깁니다. 바깥 코루틴을 취소해도 블록이 멈추지 않습니다.

```kotlin
// WithContextDetach.kt
import kotlinx.coroutines.*

fun main() = runBlocking<Unit> {
    val job = launch {
        withContext(SupervisorJob()) {
            delay(500)
            println("블록 끝까지 실행됨")
        }
    }
    delay(100)
    job.cancel()
    println("바깥 코루틴 취소")
    delay(1000)
}
```

```text
바깥 코루틴 취소
블록 끝까지 실행됨
```

정리하면 이렇습니다.

| 코드 | 블록 안 자식들의 부모 | 자식끼리 격리 | 호출한 코루틴과 연결 |
|---|---|---|---|
| `supervisorScope { }` | `SupervisorCoroutine` | 됨 | 연결됨 |
| `withContext(SupervisorJob()) { }` | 일반 코루틴 | 안 됨 | 끊김 |
| `CoroutineScope(SupervisorJob()).launch { }` | (스코프의 `SupervisorJob`) | 됨 | 끊김, 기다리지도 않음 |

함수 안에서 자식끼리 실패를 격리하면서 호출한 코루틴과의 관계도 지키는 것은 `supervisorScope { }`뿐입니다. 별도 스코프를 만드는 셋째 방법은 객체 수명에 묶을 작업에 씁니다([Q37](Q37-coroutine-scope.md#binding-lifecycle)).

## 요약 {#summary}

`supervisorScope { }`는 `coroutineScope { }`처럼 자식을 모두 기다렸다가 돌아오지만, 자식 하나의 실패가 형제를 취소하지 않습니다. 구현은 `ScopeCoroutine`을 상속하고 `childCancelled`가 `false`를 돌려주게 고친 `SupervisorCoroutine`입니다.

실패한 자식은 자기 예외를 스스로 처리합니다. `launch` 자식은 컨텍스트의 `CoroutineExceptionHandler`로, `async` 자식은 `await()`에서 던지므로, `async`와 함께 쓰면 성공한 결과만 모을 수 있습니다. 블록 본문 자체가 실패하면 자식을 모두 취소하고 예외를 던지며, 격리는 바로 아래 자식에게만 적용됩니다. `withContext(SupervisorJob())`은 모양이 비슷하지만 자식끼리 격리되지 않고 호출한 코루틴과의 연결도 끊습니다.
