# Q73) 에러 핸들링 패턴

## 에러를 다루는 두 갈래 {#intro}

에러를 다루는 방식은 크게 둘로 나뉩니다.

- **예외(exception) 기반**: 실패를 `throw`로 던지고 `try/catch`로 잡습니다. 실패가 타입 시그니처에 드러나지 않고, 호출 스택을 거슬러 올라가며 전파됩니다.
- **값(value) 기반**: 실패를 "정상값 또는 에러값"을 담는 하나의 타입으로 표현해 함수의 반환값으로 돌려줍니다. `Result`, `Either`, sealed class가 여기에 속합니다.

안드로이드에서 네트워크·DB·파싱처럼 실패가 일상적인 정상 흐름의 일부인 경우, 실패를 예외로 던지기보다 **반환 타입에 담아 호출자가 컴파일 타임에 처리하도록 강제**하는 값 기반 방식이 선호됩니다. 이 토픽은 그 도구들과 선택 기준을 다룹니다.

## kotlin.Result {#result-type}

### Result가 표현하는 것 {#what-result-is}

`kotlin.Result<T>`는 **성공값 `T` 또는 실패 `Throwable` 중 하나를 담는** 표준 라이브러리 타입입니다. 내부적으로 성공이면 값을, 실패면 `Throwable`을 감싼 단일 값(인라인 클래스)으로 표현됩니다.

```kotlin
val r: Result<Int> = runCatching { "123".toInt() }   // Success(123)
val e: Result<Int> = runCatching { "abc".toInt() }   // Failure(NumberFormatException)

r.isSuccess          // true
r.getOrNull()        // 123
e.exceptionOrNull()  // NumberFormatException
```

`runCatching { }`은 블록을 실행하다 예외가 던져지면 그것을 `Result.failure`로 포장합니다. 즉 예외를 값으로 바꾸는 변환 지점입니다.

### fold로 분기하기 {#result-fold}

`Result`의 핵심 소비 방법은 `fold`입니다. 성공과 실패 두 경우를 한 번에 처리하도록 강제하므로, 한쪽 처리를 빠뜨리기 어렵습니다.

```kotlin
val message = runCatching { api.fetchUser() }
    .fold(
        onSuccess = { user -> "환영합니다 ${user.name}" },
        onFailure = { e -> "불러오기 실패: ${e.message}" }
    )
```

`map`, `recover`, `getOrElse`, `getOrDefault` 같은 연산자로 실패를 잡지 않은 채 변환을 이어갈 수도 있습니다.

```kotlin
val count: Int = runCatching { repository.load() }
    .map { it.size }        // 성공일 때만 변환, 실패면 그대로 통과
    .getOrDefault(0)        // 실패면 0
```

### Result의 한계 — runCatching이 삼키는 것 {#result-caveat}

`runCatching`은 **모든 `Throwable`을 무차별적으로 잡습니다.** 여기에는 잡으면 안 되는 것도 포함됩니다.

```kotlin
// 위험 — CancellationException까지 삼켜 구조적 동시성을 깬다
val r = runCatching { repository.loadOnIo() }   // 코루틴 취소 신호도 Failure로 묻힘
```

코루틴 안에서 `runCatching`을 쓰면 취소 신호인 `CancellationException`까지 `Failure`로 포장해 버려, 부모가 보낸 취소가 무시됩니다. 그래서 코루틴 맥락에서는 취소를 되던지는 패턴이 필요합니다.

```kotlin
suspend fun <T> safeRunCatching(block: suspend () -> T): Result<T> =
    try {
        Result.success(block())
    } catch (e: CancellationException) {
        throw e                       // 취소 신호는 통과시킨다
    } catch (e: Throwable) {
        Result.failure(e)
    }
```

또한 `Result`의 실패 타입은 항상 `Throwable`이라 **어떤 종류의 에러인지 타입으로 구분되지 않습니다.** 도메인 에러를 분류해 다르게 처리하려면 다음의 sealed 타입이 필요합니다.

## 예외 vs sealed 에러타입 {#exception-vs-sealed}

### 예외 기반 방식 {#exception-based}

예외는 실패가 **드물고 예외적이며, 현재 함수가 합리적으로 복구할 수 없을 때** 적합합니다. 잘못된 인자(`IllegalArgumentException`), 깨진 불변식(`IllegalStateException`) 같은 프로그래밍 오류가 대표적입니다.

예외의 약점은 명료합니다.

1. **타입에 드러나지 않습니다.** `fun load(): User`라는 시그니처만 보고는 이 함수가 어떤 실패를 던지는지 알 수 없습니다. 코틀린에는 자바의 checked exception이 없어 컴파일러가 처리를 강제하지도 않습니다.
2. **누락이 조용합니다.** `catch`를 빠뜨리면 컴파일은 통과하고 런타임에 크래시로 드러납니다.
3. **분기가 흩어집니다.** 실패 처리가 호출 스택 어딘가의 `catch`로 멀리 떨어져, 어디서 어떤 에러가 처리되는지 추적하기 어렵습니다.

### sealed 에러타입 방식 {#sealed-error-type}

도메인 에러가 **여러 종류이고 호출자가 종류별로 다르게 처리해야 한다면**, 가능한 결과를 sealed 계층으로 모델링하는 것이 정확합니다.

```kotlin
sealed interface LoginResult {
    data class Success(val user: User) : LoginResult
    data object InvalidCredentials : LoginResult
    data object NetworkError : LoginResult
    data class Unknown(val cause: Throwable) : LoginResult
}
```

이 방식의 이점은 **컴파일러가 처리를 강제한다**는 점입니다. `when`으로 분기할 때 sealed 타입의 모든 갈래를 다루지 않으면, 분기 결과를 값으로 쓰는 위치에서 컴파일 에러가 납니다.

```kotlin
val text = when (result) {            // 한 갈래라도 빠지면 컴파일 에러
    is LoginResult.Success -> "환영합니다"
    LoginResult.InvalidCredentials -> "비밀번호가 틀렸습니다"
    LoginResult.NetworkError -> "네트워크를 확인하세요"
    is LoginResult.Unknown -> "오류: ${result.cause.message}"
}
```

새 에러 케이스를 sealed 타입에 추가하는 순간, 그것을 처리하지 않은 모든 `when`이 컴파일 에러로 드러납니다. 이것이 예외 대비 가장 큰 실무적 이득입니다.

### 선택 기준 {#choosing}

| 상황 | 권장 방식 |
|------|-----------|
| 프로그래밍 오류 (불변식 위반, 잘못된 인자) | 예외 (`throw`) — 복구 대상 아님, 빠르게 실패 |
| 단일 실패만 있고 호출자가 구분 불필요 | `Result<T>` |
| 도메인 실패가 여러 종류, 종류별 분기 필요 | sealed 에러타입 |
| 라이브러리/시스템 경계에서 들어오는 예외 | `runCatching`/`try`로 잡아 값 타입으로 변환 |

원칙은 **"예상되는 실패는 값으로, 예상 못 한 버그는 예외로"** 입니다. 비즈니스 흐름의 일부인 실패(잘못된 비밀번호, 오프라인)는 sealed 타입으로 모델링하고, 일어나선 안 되는 상태는 예외로 던져 크래시·로깅으로 드러냅니다.

## 함수형 에러처리와 Either {#functional-either}

### Either란 {#what-either}

`Either<L, R>`는 **두 타입 중 하나를 담는** 합 타입(sum type)입니다. 관례적으로 왼쪽(`Left`)에 실패를, 오른쪽(`Right`)에 성공을 둡니다("right = 옳다 = 성공"). 코틀린 표준 라이브러리에는 없고 [Arrow](https://arrow-kt.io/) 라이브러리가 제공합니다.

`Result`와의 핵심 차이는 **실패 타입을 자유롭게 정할 수 있다**는 점입니다. `Result`의 실패는 항상 `Throwable`이지만, `Either`의 왼쪽은 위에서 만든 sealed 도메인 에러를 그대로 쓸 수 있습니다.

```kotlin
sealed interface UserError {
    data object NotFound : UserError
    data object Unauthorized : UserError
}

fun findUser(id: String): Either<UserError, User> =
    if (id.isBlank()) UserError.NotFound.left()
    else User(id).right()
```

### 합성: 에러를 전파하며 변환을 이어 붙이기 {#either-composition}

함수형 에러처리의 핵심은 **여러 실패 가능 연산을 연결할 때, 중간에 실패가 나오면 나머지를 건너뛰고 그 실패를 그대로 흘려보내는** 것입니다. `try/catch` 없이 정상 흐름만 기술하면 됩니다.

```kotlin
// 모든 단계가 Either를 반환. 한 단계라도 Left면 즉시 그 Left를 반환
fun loadProfile(id: String): Either<UserError, Profile> =
    findUser(id).flatMap { user ->          // user가 있을 때만 다음으로
        loadProfileOf(user)                 // 이 단계도 Either<UserError, Profile>
    }
```

Arrow의 `either { }` 블록과 `.bind()`를 쓰면 이 연결을 절차적 코드처럼 평탄하게 쓸 수 있습니다. `.bind()`는 `Right`면 값을 꺼내 다음 줄로 진행하고, `Left`면 블록 전체를 즉시 그 `Left`로 종료시킵니다.

```kotlin
fun loadProfile(id: String): Either<UserError, Profile> = either {
    val user = findUser(id).bind()          // Left면 여기서 함수가 그 Left 반환
    val profile = loadProfileOf(user).bind()
    profile                                 // 모두 Right면 Right(profile)
}
```

### 왜 함수형 방식인가 {#why-functional}

이 방식이 주는 것은 세 가지입니다.

1. **실패가 시그니처에 명시됩니다.** `Either<UserError, Profile>`만 보고 어떤 도메인 에러가 가능한지 알 수 있습니다.
2. **처리 누락이 컴파일 타임에 막힙니다.** 결과를 소비하려면 `fold`나 `when`으로 양쪽을 다뤄야 합니다.
3. **에러 전파가 자동입니다.** 단계마다 `if (실패) return`을 쓰지 않아도 `bind`/`flatMap`이 단축 평가(short-circuit)로 실패를 흘려보냅니다.

다만 외부 의존성(Arrow)이 추가되고 팀이 합 타입 합성에 익숙해야 합니다. 의존성을 늘리지 않으려면 sealed 타입 + `when`만으로도 1·2번 이득은 그대로 얻을 수 있습니다. 3번의 자동 전파가 코드를 크게 줄여 줄 때 `Either`가 값을 합니다.

## 요약 {#summary}

> **TL;DR** — 에러는 예외로 던지거나 값으로 반환할 수 있습니다. 예상되는 실패는 값으로 다루는 편이 안전합니다. 단일 실패만 있으면 `Result<T>`(실패 타입은 항상 `Throwable`, `runCatching`은 `CancellationException`까지 삼키니 주의), 도메인 실패가 여러 종류면 sealed 에러타입으로 모델링해 컴파일러가 분기 누락을 잡게 합니다. 실패 타입을 직접 정하고 여러 연산을 자동 전파로 합성하려면 Arrow의 `Either`와 `bind`를 씁니다.

1. **kotlin.Result**: 성공값 또는 `Throwable`을 담는 표준 타입. `runCatching`으로 예외를 값으로 바꾸고 `fold`로 소비한다. 단, 모든 `Throwable`을 잡으므로 코루틴에서는 `CancellationException`을 되던져야 한다.
2. **예외 vs sealed 에러타입**: 복구 불가한 프로그래밍 오류는 예외로, 호출자가 종류별로 분기해야 하는 도메인 실패는 sealed 타입으로. sealed 타입은 `when` 분기 누락을 컴파일 타임에 잡아 준다.
3. **함수형 에러처리(Either)**: 실패 타입을 직접 정할 수 있는 합 타입. `flatMap`/`bind`가 실패를 단축 평가로 자동 전파해, `try/catch` 없이 정상 흐름만 기술하면 된다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 예외(throw)와 Result·sealed 같은 값 기반 에러처리는 각각 언제 쓰나요?">

기준은 "그 실패가 예상되는 정상 흐름의 일부인가, 일어나선 안 되는 버그인가"입니다. 잘못된 인자나 깨진 불변식처럼 현재 함수가 복구할 수 없는 프로그래밍 오류는 예외로 던져 빠르게 실패시키고 크래시·로깅으로 드러내는 편이 낫습니다.

반면 네트워크 실패, 잘못된 비밀번호, 캐시 미스처럼 비즈니스 흐름에서 일상적으로 발생하는 실패는 값으로 반환하는 편이 안전합니다. 예외는 타입 시그니처에 드러나지 않고 코틀린에는 checked exception이 없어 처리를 빠뜨려도 컴파일이 통과하지만, `Result`나 sealed 타입으로 반환하면 호출자가 실패를 컴파일 타임에 인지하고 처리하도록 강제됩니다.

</def>
<def title="Q) kotlin.Result를 코루틴 안에서 쓸 때 주의할 점은 무엇인가요?">

`runCatching`이 모든 `Throwable`을 무차별로 잡는다는 점입니다. 코루틴의 취소는 `CancellationException`을 던져 동작하는데, `runCatching`이 이것까지 `Result.failure`로 포장해 버리면 부모가 보낸 취소가 무시되어 구조적 동시성의 취소 보장이 깨집니다.

따라서 코루틴 맥락에서는 `CancellationException`을 먼저 잡아 되던지고(`throw e`) 나머지 `Throwable`만 `Result.failure`로 감싸는 안전한 래퍼를 써야 합니다. 또한 `Result`의 실패 타입은 항상 `Throwable`이라 에러 종류를 타입으로 구분할 수 없으므로, 종류별 분기가 필요하면 sealed 에러타입이나 `Either`가 더 적합합니다.

</def>
<def title="Q) sealed 에러타입이 예외 기반 처리보다 나은 점은 무엇인가요?">

컴파일러가 모든 에러 케이스의 처리를 강제한다는 점입니다. 가능한 결과를 sealed 계층으로 모델링하고 `when`으로 분기하면, 한 갈래라도 다루지 않을 때 분기 결과를 값으로 쓰는 위치에서 컴파일 에러가 납니다.

실무에서 가장 큰 이득은 진화 시점에 드러납니다. 새 에러 케이스를 sealed 타입에 추가하는 순간, 그 케이스를 처리하지 않은 모든 `when`이 컴파일 에러로 표시되어 어디를 고쳐야 하는지 즉시 알 수 있습니다. 예외 기반에서는 새 예외를 추가해도 컴파일러가 아무것도 알려주지 않아 처리 누락이 런타임 크래시로만 드러납니다.

</def>
<def title="Q) Either는 kotlin.Result와 무엇이 다르고, 함수형 에러처리의 이점은 무엇인가요?">

가장 큰 차이는 실패 타입의 자유도입니다. `Result`의 실패는 항상 `Throwable`로 고정되지만, `Either<L, R>`의 왼쪽(`L`)에는 직접 정의한 sealed 도메인 에러를 넣을 수 있어 실패를 의미 있는 타입으로 표현할 수 있습니다.

함수형 에러처리의 이점은 합성과 자동 전파입니다. 실패 가능한 연산들을 `flatMap`이나 Arrow의 `either { }` 블록 안 `.bind()`로 연결하면, 중간 단계가 `Left`(실패)인 순간 나머지를 건너뛰고 그 실패를 그대로 반환하는 단축 평가가 일어납니다. 덕분에 단계마다 `if (실패) return`을 쓰지 않고 정상 흐름만 평탄하게 기술하면 됩니다. 다만 Arrow 의존성이 추가되므로, 자동 전파가 코드를 충분히 줄여 줄 때 도입 가치가 있습니다.

</def>
</deflist>
