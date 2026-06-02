# E9) Sealed Class와 타입 안정성

## Sealed Class 기초 {#sealed-basics}

`sealed class`(봉인 클래스)는 **하위 타입의 집합이 컴파일 시점에 고정되는 클래스**입니다. `sealed`로 선언하면 그 클래스를 상속하는 하위 클래스는 **같은 모듈, 같은 패키지 안에서만** 정의할 수 있습니다. 외부 모듈이나 다른 패키지에서는 상속할 수 없으므로, 컴파일러는 "이 타입이 가질 수 있는 하위 타입의 전체 목록"을 빠짐없이 알 수 있습니다.

```kotlin
sealed class Result
data class Success(val data: String) : Result()
data class Failure(val error: Throwable) : Result()
object Loading : Result()
```

이 "닫힌 계층(closed hierarchy)"이라는 성질이 이 토픽의 모든 이점의 출발점입니다. 하위 타입이 고정돼 있기 때문에 `when`이 모든 경우를 다뤘는지 컴파일러가 검증할 수 있고(망라성), 그 덕분에 상태를 타입으로 안전하게 모델링할 수 있습니다.

- **`sealed class`**: 추상 클래스처럼 생성자 파라미터와 상태를 가질 수 있습니다. 하위 타입이 각자 다른 프로퍼티를 가질 때 사용합니다.
- **`sealed interface`**: Kotlin 1.5부터 추가됐습니다. 클래스가 여러 봉인 계층에 동시에 속해야 할 때(다중 상속) 사용합니다.

> 하위 타입이 인스턴스를 하나만 가지면 `object`로, 상태를 담아야 하면 `class`/`data class`로 선언합니다. 위 예의 `Loading`처럼 데이터가 없는 상태는 `object`가 적합합니다.

## sealed class vs enum {#sealed-vs-enum}

둘 다 "정해진 종류의 집합"을 표현하지만, 표현할 수 있는 대상이 근본적으로 다릅니다.

### enum: 고정된 인스턴스의 집합 {#enum-instances}

`enum class`는 **미리 정의된 상수 인스턴스들의 유한한 집합**입니다. 각 상수는 싱글턴이며, 모든 상수는 같은 타입·같은 프로퍼티 구조를 공유합니다.

```kotlin
enum class HttpMethod(val safe: Boolean) {
    GET(safe = true),
    POST(safe = false),
    DELETE(safe = false)
}
```

`enum`의 한계는 **각 상수가 서로 다른 형태의 데이터를 담을 수 없다**는 점입니다. 모든 상수가 동일한 생성자를 공유하므로, "GET은 캐시 키를 갖고 POST는 바디를 갖는다" 같은 구조는 표현할 수 없습니다.

### sealed class: 서로 다른 타입의 집합 {#sealed-types}

`sealed class`의 하위 타입은 **각자 독립된 클래스**이므로 서로 다른 프로퍼티를 가질 수 있고, 같은 하위 타입의 인스턴스를 여러 개 만들 수 있습니다.

```kotlin
sealed class Payment
data class Card(val number: String, val cvc: String) : Payment()
data class Bank(val account: String) : Payment()
object Cash : Payment()
```

`Card`와 `Bank`는 담는 데이터의 형태 자체가 다릅니다. 이것이 `enum`으로는 불가능하고 `sealed class`로만 가능한 핵심 차이입니다.

### 선택 기준 {#sealed-enum-criteria}

| 구분 | enum class | sealed class |
|------|-----------|--------------|
| 표현 대상 | 고정된 상수 인스턴스 | 서로 다른 타입의 계층 |
| 하위 타입별 다른 데이터 | 불가 (생성자 공유) | 가능 |
| 인스턴스 개수 | 상수당 정확히 1개 | 하위 타입당 다수 가능 |
| `when` 망라성 검사 | 지원 | 지원 |
| `values()` / 순회 | 가능 | 불가 (직접 나열해야 함) |

정리하면, **케이스마다 담을 데이터가 다르면 `sealed`, 단순히 이름 붙은 상수 목록이면 `enum`**입니다. 상수 전체를 순회(`values()`)해야 하는 상황은 `enum`이 더 적합합니다. `sealed`는 하위 타입을 자동으로 나열하는 표준 stdlib API가 없어, 전체 순회가 필요하면 직접 나열하거나 `Result::class.sealedSubclasses`(리플렉션)에 의존해야 합니다.

## when 망라성(exhaustiveness) {#when-exhaustiveness}

`sealed`의 가장 실용적인 이점은 `when`의 **망라성 검사**입니다. 봉인 계층은 하위 타입이 닫혀 있으므로, 컴파일러가 "모든 하위 타입을 다뤘는지"를 검증할 수 있습니다.

```kotlin
fun render(result: Result): String = when (result) {
    is Success -> result.data
    is Failure -> result.error.message ?: "unknown"
    Loading    -> "loading..."
    // 모든 하위 타입을 다뤘으므로 else가 필요 없다
}
```

### else 없이 컴파일된다는 것의 의미 {#no-else-branch}

`when`을 **식(expression)으로 사용**하면(값을 반환하거나 변수에 대입하면) Kotlin은 망라성을 강제합니다. sealed 계층의 모든 하위 타입을 다루면 `else` 가지가 필요 없습니다. 여기서 진짜 이점이 나옵니다.

**나중에 하위 타입을 추가하면, 그 타입을 처리하지 않은 모든 `when`이 컴파일 에러가 됩니다.**

```kotlin
// 새 상태 추가
object Empty : Result()

// 위 render()의 when은 이제 컴파일 에러:
// "'when' expression must be exhaustive, add 'is Empty' branch"
```

이것이 `enum`/`sealed`가 주는 안전성의 핵심입니다. `else -> ...`로 뭉뚱그리면 컴파일러가 누락을 잡아 줄 수 없으므로, **새 케이스를 빠뜨려도 런타임까지 드러나지 않습니다.** 망라성을 활용하려면 의미 없는 `else`를 남발하지 않아야 합니다.

> **문(statement)으로 쓴 `when`** 의 망라성은 버전에 따라 다릅니다. Kotlin 1.6은 sealed/enum 대상의 비망라적 statement `when`에 대해 **경고(warning)** 를 도입했고, Kotlin 1.7부터는 이를 **에러(error)로 강제**합니다. 다만 statement 형태에서는 누락이 경고로만 보일 수 있는 구간이 있으니, 의도적으로 `when`을 식으로 만드는 패턴(반환값 사용)이 버전과 무관하게 가장 안전합니다.

## sealed로 상태 모델링 {#state-modeling}

안드로이드에서 `sealed`가 가장 많이 쓰이는 곳은 **UI 상태와 비동기 결과를 하나의 타입으로 모델링**하는 것입니다.

### 불가능한 상태를 표현 불가능하게 만든다 {#illegal-states-unrepresentable}

흔한 안티패턴은 화면 상태를 여러 개의 nullable·boolean 플래그로 흩어 놓는 것입니다.

```kotlin
// 안티패턴: 모순된 상태가 표현 가능하다
data class UiState(
    val isLoading: Boolean,
    val data: List<Item>?,
    val error: String?
)
// isLoading=true 인데 data와 error가 동시에 채워진 상태?
// 로딩도 아니고 데이터도 에러도 없는 상태? — 모두 컴파일된다
```

`isLoading=true`이면서 `error`도 채워진 모순 상태가 타입상 허용됩니다. 이런 조합을 매번 방어 코드로 걸러야 합니다.

`sealed`로 바꾸면 **유효한 상태만 타입으로 존재**하게 됩니다.

```kotlin
sealed interface UiState {
    object Loading : UiState
    data class Content(val items: List<Item>) : UiState
    data class Error(val message: String) : UiState
}
```

이제 "로딩이면서 동시에 에러"인 상태는 **만들 수가 없습니다.** 각 상태가 자신에게 필요한 데이터만 정확히 들고 있으므로, 모순된 조합을 검사하는 방어 코드가 사라집니다. 이 원칙을 "불가능한 상태를 표현 불가능하게 만든다(make illegal states unrepresentable)"라고 부릅니다.

### 상태에 따라 데이터가 강제된다 {#state-bound-data}

`when`으로 상태를 분기하면, 스마트 캐스트 덕분에 **그 상태에만 존재하는 데이터에 안전하게 접근**할 수 있습니다.

```kotlin
fun bind(state: UiState) = when (state) {
    UiState.Loading    -> showSpinner()
    is UiState.Content -> showList(state.items)     // items는 Content에만 있다
    is UiState.Error   -> showError(state.message)  // message는 Error에만 있다
}
```

`Content` 가지 안에서만 `items`에 접근할 수 있으므로, "데이터가 없는데 리스트를 그리는" 실수가 타입 수준에서 차단됩니다.

## 널 안정성과의 결합 {#null-safety}

`sealed`는 Kotlin의 널 안정성과 결합해 `null`의 의미적 모호함을 제거합니다.

### null 대신 명시적 케이스 {#explicit-cases-over-null}

값이 없거나 실패했음을 `null`로 표현하면, `null` 하나에 "아직 안 불러옴", "비어 있음", "에러" 같은 여러 의미가 뒤섞입니다. 호출자는 이 중 무엇인지 알 수 없습니다.

```kotlin
// null의 의미가 모호하다
fun findUser(id: String): User?   // 못 찾음? 네트워크 실패? 둘 다 null
```

`sealed`로 결과를 모델링하면 각 경우가 **고유한 타입**이 되어 의미가 분명해지고, `when` 망라성이 모든 경우의 처리를 강제합니다.

```kotlin
sealed interface UserResult {
    data class Found(val user: User) : UserResult
    object NotFound : UserResult
    data class Failed(val cause: Throwable) : UserResult
}
```

### nullable과 스마트 캐스트 {#nullable-smart-cast}

`sealed` 계층 안에서도 nullable 프로퍼티는 쓸 수 있지만, **상태 분리로 nullable 자체를 줄이는 방향**이 더 안전합니다. nullable이 남아 있을 때는 Kotlin의 스마트 캐스트가 분기 안에서 non-null로 좁혀 줍니다.

```kotlin
sealed interface AuthState {
    object LoggedOut : AuthState
    data class LoggedIn(val token: String) : AuthState  // token은 항상 non-null
}

fun header(state: AuthState): String? = when (state) {
    AuthState.LoggedOut   -> null
    is AuthState.LoggedIn -> "Bearer ${state.token}"   // token을 ?로 검사할 필요 없다
}
```

`token`을 `String?`로 두고 "로그인했지만 토큰이 null"인 모순을 매번 검사하는 대신, **토큰이 있는 상태(`LoggedIn`)에만 non-null `token`을 둠**으로써 nullable 검사 자체를 제거했습니다. 이것이 `sealed`와 널 안정성이 함께 만드는 핵심 효과입니다. 상태를 타입으로 쪼개면 "그 상태에서 반드시 존재하는 값"은 non-null로 둘 수 있습니다.

## 요약 {#summary}

> **TL;DR** — `sealed`는 하위 타입이 컴파일 시점에 고정되는 닫힌 계층입니다. 그래서 `when`이 모든 케이스를 다뤘는지 컴파일러가 검증(망라성)하고, 케이스를 추가하면 처리 누락이 컴파일 에러로 드러납니다. `enum`이 동일 구조의 상수 집합이라면 `sealed`는 케이스마다 다른 데이터를 담는 타입의 집합입니다. UI/비동기 상태를 `sealed`로 모델링하면 모순된 상태와 모호한 `null`을 타입 수준에서 제거할 수 있습니다.

1. **sealed vs enum**: enum은 같은 구조의 상수 인스턴스 집합, sealed는 케이스마다 다른 데이터를 담는 타입의 집합이다. 케이스별 데이터가 다르면 sealed, 단순 상수 목록이면 enum.
2. **when 망라성**: 닫힌 계층 덕분에 `when`을 식으로 쓰면 모든 하위 타입 처리를 컴파일러가 강제한다. 케이스를 추가하면 누락된 `when`이 컴파일 에러가 된다 — 그래서 의미 없는 `else`를 피해야 한다.
3. **상태 모델링**: 흩어진 boolean/nullable 플래그 대신 sealed로 상태를 쪼개면, 모순된 상태를 표현 불가능하게 만들고 각 상태가 필요한 데이터만 정확히 들게 한다.
4. **널 안정성**: "값 없음/실패"를 모호한 `null` 대신 명시적 케이스로 표현하고, 그 상태에 반드시 존재하는 값은 non-null로 둬 nullable 검사를 제거한다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) sealed class와 enum class의 차이는 무엇이고, 언제 어느 것을 쓰나요?">

`enum class`는 미리 정의된 상수 인스턴스들의 유한한 집합으로, 모든 상수가 같은 생성자·같은 프로퍼티 구조를 공유합니다. 따라서 케이스마다 다른 형태의 데이터를 담을 수 없습니다.

`sealed class`의 하위 타입은 각자 독립된 클래스이므로 서로 다른 프로퍼티를 가질 수 있고, 같은 하위 타입의 인스턴스를 여러 개 만들 수 있습니다. 둘 다 `when` 망라성 검사를 지원하지만, 케이스마다 담을 데이터가 다르면 sealed, 단순히 이름 붙은 상수 목록이고 전체를 `values()`로 순회해야 하면 enum이 적합합니다.

</def>
<def title="Q) sealed class에서 when에 else를 쓰지 않는 게 왜 더 안전한가요?">

sealed는 하위 타입이 컴파일 시점에 고정되는 닫힌 계층이라, `when`을 식으로 쓰면 컴파일러가 모든 하위 타입을 다뤘는지 검증합니다. 모든 케이스를 다루면 `else`가 필요 없습니다.

이 상태에서 새 하위 타입을 추가하면, 그 타입을 처리하지 않은 모든 `when`이 즉시 컴파일 에러가 됩니다. 누락을 컴파일 시점에 잡아 주는 것입니다. 반면 `else -> ...`로 뭉뚱그리면 새 케이스도 `else`로 흡수되어 컴파일러가 누락을 알려 줄 수 없고, 처리 빠짐이 런타임까지 드러나지 않습니다. 그래서 망라성을 살리려면 의미 없는 `else`를 피해야 합니다.

</def>
<def title="Q) UI 상태를 sealed로 모델링하면 boolean 플래그 묶음보다 무엇이 좋아지나요?">

`isLoading: Boolean`, `data: List?`, `error: String?` 같은 플래그 묶음은 "로딩이면서 동시에 에러"처럼 모순된 조합도 타입상 허용합니다. 그래서 매번 어떤 조합이 유효한지 방어 코드로 걸러야 합니다.

sealed로 `Loading` / `Content(items)` / `Error(message)`처럼 상태를 쪼개면 유효한 상태만 타입으로 존재하게 되어, 모순 조합을 아예 만들 수 없습니다(불가능한 상태를 표현 불가능하게 만들기). 또한 각 상태가 자신에게 필요한 데이터만 들고 있으므로, `when` 분기 안에서 스마트 캐스트로 그 데이터에 안전하게 접근할 수 있고 모순 검사 코드가 사라집니다.

</def>
<def title="Q) sealed class는 널 안정성과 어떻게 결합되나요?">

값이 없거나 실패했음을 `null` 하나로 표현하면, 그 `null`에 "아직 안 불러옴", "비어 있음", "에러" 같은 여러 의미가 섞여 호출자가 무엇인지 구분할 수 없습니다.

sealed로 `Found(user)` / `NotFound` / `Failed(cause)`처럼 각 경우를 고유한 타입으로 표현하면 의미가 분명해지고, `when` 망라성이 모든 경우의 처리를 강제합니다. 더 나아가 어떤 상태에 반드시 존재하는 값은 그 상태 타입 안에서 non-null로 둘 수 있습니다. 예를 들어 `LoggedIn(token: String)`처럼 두면 "로그인했지만 토큰이 null"인 모순이 사라지고, 매번 `?`로 토큰을 검사할 필요가 없어집니다.

</def>
</deflist>
