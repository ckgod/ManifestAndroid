# Q0) null 안정성

> **먼저 읽으면 좋아요** — `null`이 정확히 무엇인지, "null을 참조한다"는 게 어떤 의미인지, 그리고 `Int`·`Boolean` 같은 원시 타입도 nullable하게 만들 수 있는지는 [Details) null과 참조, 그리고 원시 타입](Details-null과-참조.md)에서 다룹니다. 이 개념이 익숙하지 않다면 먼저 보고 오는 것을 권합니다.

## null 안정성이 필요한 이유 {#why-null-safety}

JVM 환경에서 가장 악명 높은 오류를 하나 꼽으라면 단연 `NullPointerException`(NPE)입니다. 아무것도 가리키지 않는 참조, 즉 `null`인 참조의 멤버에 접근하려다 발생하죠. 수십 년 동안 개발자들은 이를 막기 위해 방어적이고 반복적인 null 검사를 코드 곳곳에 넣어 왔습니다.

Kotlin은 접근 방식이 근본적으로 다릅니다. `null`을 **런타임에 방어해야 할 문제**로 두는 대신, **nullable 개념을 타입 시스템에 직접 통합**했습니다. 그 결과 null 안정성 검사의 부담이 개발자에서 컴파일러로 옮겨 가고, 상당수의 NPE를 **컴파일 시점**에 차단할 수 있게 됩니다.

> **10억 달러짜리 실수** — `null` 참조는 컴퓨터 과학자 Tony Hoare가 1965년에 도입한 개념으로, 그는 훗날 이를 "10억 달러짜리 실수(Billion-Dollar Mistake)"라고 불렀습니다. 그동안 무수한 NPE를 유발해 개발·디버깅·운영에 막대한 비용을 초래했기 때문입니다. Kotlin의 null 안정성은 바로 이 문제를 언어 차원에서 해결하려는 시도입니다.

## 두 가지 타입: non-nullable과 nullable {#two-types}

Kotlin의 null 안정성은 **`null`을 담을 수 있는 참조와 담을 수 없는 참조를 명시적으로 구분**하는 데서 출발합니다. 이 구분은 단순한 관례가 아니라 타입 시스템의 일부이며, 컴파일러가 언어 수준에서 강제합니다.

### non-nullable 타입 (기본값) {#non-nullable}

Kotlin에서 선언하는 모든 타입은 **기본적으로 non-nullable**입니다. 명시적으로 달리 표시하지 않는 한, 변수에는 항상 유효한 인스턴스가 담겨 있다고 보장됩니다.

```kotlin
// non-nullable String — 반드시 String 값을 담아야 한다
var name: String = "Kotlin"

name = null // 컴파일 에러: Null can not be a value of a non-null type String
```

이 간단한 규칙이 언어를 크게 바꿉니다. 컴파일러가 `null`이 아님을 보장해 주므로, 코드 대부분에서 NPE 걱정 없이 `name.length`처럼 프로퍼티와 메서드에 직접 접근할 수 있습니다.

### nullable 타입 (`?`) {#nullable}

물론 값이 없을 수 있는 상황도 있습니다. 중간 이름이 없는 사용자, 결과를 찾지 못한 DB 쿼리처럼요. 이런 경우를 표현하려면 타입 뒤에 물음표(`?`)를 붙여 **nullable**로 선언합니다.

```kotlin
// nullable String — String 또는 null을 담을 수 있다
var middleName: String? = "J."
middleName = null // 정상 동작
```

`String?`으로 선언하는 것은 컴파일러에게 "이 변수는 null일 수 있으니, 사용하는 쪽은 그 가능성을 반드시 처리하라"고 알리는 것입니다. 그래서 `middleName.length`처럼 **직접 접근하면 컴파일 에러**가 납니다.

```kotlin
middleName.length
// 컴파일 에러: Only safe (?.) or non-null asserted (!!.) calls are
// allowed on a nullable receiver of type String?
```

이 컴파일 타임 검사가 NPE를 막는 핵심 장치입니다. nullable 값에 접근하려면 아래의 안전한 방법 중 하나를 반드시 거쳐야 합니다.

## nullable을 안전하게 다루기 {#handling-nullable}

컴파일러가 nullable에 대한 직접 접근을 막는 대신, Kotlin은 이를 간결하게 다룰 수 있는 연산자들을 언어 차원에서 제공합니다.

### 안전 호출 연산자 `?.` {#safe-call}

가장 일반적인 방법입니다. 객체가 `null`이 아니면 연산을 그대로 수행하고, `null`이면 **연산을 건너뛴 채 전체 표현식이 `null`로 평가**됩니다(멤버가 아예 호출되지 않습니다).

```kotlin
val nickname: String? = null
val length: Int? = nickname?.length // length는 null (호출 자체가 일어나지 않음)

val realName: String? = "skydoves"
val realLength: Int? = realName?.length // 9
```

체이닝도 가능해서, 중간 어느 하나라도 `null`이면 안전하게 `null`을 반환합니다.

```kotlin
// user, profile, address 중 하나라도 null이면 결과는 null
val street: String? = user?.profile?.address?.street
```

### Elvis 연산자 `?:` {#elvis}

값이 `null`일 때 `null`을 그대로 전파하는 대신 **기본값·대체값을 주고 싶을 때** 사용합니다. 왼쪽이 `null`이 아니면 그 값을, `null`이면 오른쪽 값을 반환하는 이항 연산자입니다.

```kotlin
val userDisplayName: String? = null
val nameToDisplay: String = userDisplayName ?: "Guest" // "Guest"

// 안전 호출과 함께 쓰는 조합이 특히 흔하다
val user: User? = null
val userName: String = user?.name ?: "Anonymous User" // "Anonymous User"
```

`?.`와 `?:`의 조합은 nullable 데이터에 안전하게 접근하면서 **non-null 결과를 보장**하는 가장 간결한 관용구입니다.

> **이름의 유래** — 연산자 `?:`를 90도 돌려 보면 물결 모양 앞머리를 한 Elvis Presley의 옆모습처럼 보인다고 해서 "Elvis 연산자"라 부릅니다.

### not-null 단언 연산자 `!!` {#not-null-assertion}

특정 지점에서 값이 절대 `null`이 아니라고 **확신할 때** 쓰는 연산자입니다. nullable 타입을 non-nullable로 변환해 멤버에 직접 접근하게 해 줍니다.

```kotlin
val user: User? = getUser()
val name: String = user!!.name // "이 값은 절대 null이 아니다"라고 단언

val nullUser: User? = null
val nameFromNull: String = nullUser!!.name // 런타임에 NullPointerException!
```

이 연산자는 컴파일러에게 "날 믿어, 이 한 줄은 안전 검사를 꺼도 돼"라고 말하는 것과 같습니다. 단언이 틀려 값이 실제로 `null`이면 **런타임에 NPE가 터지고 앱이 크래시**합니다. Kotlin이 타입 안정성으로 없애려던 문제를 다시 불러오는 셈이라, `!!`를 남발하는 것은 흔히 **코드 스멜**로 간주됩니다. 대부분은 아래의 스마트 캐스트나 `?.`·`?:`로 대체할 수 있습니다.

### 스마트 캐스트와 안전한 캐스트 {#smart-cast}

Kotlin 컴파일러는 명시적인 `null` 검사를 인식해, 검사가 참인 범위 안에서는 변수를 자동으로 non-nullable로 **스마트 캐스트**합니다. `?.`나 `!!` 없이 바로 접근할 수 있게 되는 것이죠.

```kotlin
val user: User? = findUser()

if (user != null) {
    // 이 블록 안에서 user는 non-null로 스마트 캐스트된다
    println("Welcome, ${user.name}") // ?. 나 !! 불필요
}
```

타입 캐스트에도 안전한 형태가 있습니다. `as?`(안전한 캐스트 연산자)는 캐스트가 불가능할 때 `ClassCastException`을 던지는 대신 **`null`을 반환**합니다.

```kotlin
val obj: Any = "hello"
val n: Int? = obj as? Int   // 캐스트 실패 → null (예외 없음)
val s: String? = obj as? String // 성공 → "hello"
```

## Java 상호운용과 플랫폼 타입 {#platform-types}

Kotlin의 강점 중 하나는 Java와의 매끄러운 상호운용입니다. 그런데 Java의 타입 시스템에는 null 안정성이 내장돼 있지 않습니다. 그렇다면 객체를 반환하는 Java 메서드를 호출할 때, 그 값이 `null`일 수 있는지 Kotlin은 어떻게 알까요?

이 모호함을 처리하려고 Kotlin은 **플랫폼 타입(platform type)** 개념을 둡니다. Java에서 온 타입은 nullability를 알 수 없는 것으로 취급되며, IDE에서는 느낌표 하나로 표시됩니다(예: `String!`). 플랫폼 타입은 "유연한" 타입이라, 개발자가 nullable(`String?`)로 다룰지 non-nullable(`String`)로 다룰지 스스로 선택합니다.

이 유연함은 실용적인 타협이지만, **Kotlin 코드에서도 NPE가 발생할 수 있는 위험 지점**이기도 합니다. 플랫폼 타입을 non-nullable로 취급했는데 실제로 Java가 `null`을 반환하면 런타임 예외가 나기 때문입니다.

> **원칙** — Java API가 `@NonNull` / `@Nullable` 같은 nullability 어노테이션(Kotlin이 이해하고 존중합니다)으로 명시되지 않은 한, **Java에서 오는 모든 값은 nullable로 취급**하는 방어적 접근이 가장 안전합니다.

## 요약 {#summary}

> **TL;DR** — Kotlin은 nullability를 타입 시스템에 통합해, `null`을 담을 수 있는 타입(`String?`)과 없는 타입(`String`)을 명시적으로 구분합니다. non-nullable이 기본이고, nullable에 직접 접근하면 컴파일 에러가 납니다. 안전 호출(`?.`), Elvis(`?:`), 스마트 캐스트로 nullable을 안전하게 다루며, `!!`는 확신할 때만 쓰는 최후 수단입니다. Java 상호운용에서 오는 플랫폼 타입은 여전히 NPE의 통로이므로 nullable로 방어하는 것이 안전합니다.

1. **두 가지 타입**: 모든 타입은 기본이 non-nullable이고, `?`를 붙여야 nullable이 된다. nullable에 직접 접근하면 컴파일러가 막는다 — 이것이 NPE를 컴파일 시점에 잡는 핵심이다.
2. **`?.` (안전 호출)**: 수신 객체가 null이면 호출을 건너뛰고 전체 식이 null이 된다. 체이닝으로 중첩 객체를 안전하게 탐색할 수 있다.
3. **`?:` (Elvis)**: null일 때 대체값을 제공한다. `user?.name ?: "Guest"`처럼 `?.`와 결합해 non-null 결과를 보장하는 관용구가 흔하다.
4. **`!!` (not-null 단언)**: nullable을 non-null로 강제 변환하지만, 틀리면 런타임 NPE. 남발은 코드 스멜이며 스마트 캐스트나 `?.`·`?:`로 대체하는 편이 낫다.
5. **스마트 캐스트 / `as?`**: `if (x != null)` 범위 안에서는 자동으로 non-null로 좁혀진다. `as?`는 캐스트 실패 시 예외 대신 null을 반환한다.
6. **플랫폼 타입**: Java에서 온 값은 nullability를 알 수 없어 `String!`로 표시된다. 어노테이션이 없으면 nullable로 취급해 방어하는 것이 안전하다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Kotlin은 NPE를 어떻게 컴파일 시점에 막나요?">

Kotlin은 nullability를 타입 시스템에 직접 통합했습니다. `null`을 담을 수 있는 타입(`String?`)과 담을 수 없는 타입(`String`)을 명시적으로 구분하고, 이 구분을 컴파일러가 언어 수준에서 강제합니다.

기본적으로 모든 타입은 non-nullable이라 `null`을 대입하면 컴파일 에러가 납니다. nullable 타입은 안전 호출(`?.`)이나 non-null 단언(`!!`) 없이 멤버에 직접 접근하면 역시 컴파일 에러가 납니다. 즉 null 검사의 부담이 개발자의 방어 코드에서 컴파일러로 옮겨 가, 상당수의 NPE가 런타임 이전에 차단됩니다.

</def>
<def title="Q) 안전 호출(?.)과 Elvis(?:) 연산자는 각각 어떻게 동작하나요?">

**안전 호출 `?.`** 은 수신 객체가 `null`이 아니면 연산을 수행하고, `null`이면 멤버 호출 자체를 건너뛴 채 전체 표현식을 `null`로 평가합니다. 체이닝(`a?.b?.c`)하면 중간 어느 하나라도 `null`일 때 안전하게 `null`을 반환합니다.

**Elvis `?:`** 는 왼쪽 표현식이 `null`이 아니면 그 값을, `null`이면 오른쪽 값을 반환합니다. 둘을 결합한 `user?.name ?: "Guest"`는 nullable에 안전하게 접근하면서 결과를 non-null로 보장하는 대표적인 관용구입니다.

</def>
<def title="Q) not-null 단언(!!)은 왜 신중하게 써야 하나요?">

`!!` 는 nullable 타입을 non-nullable로 강제 변환해 직접 접근을 허용합니다. 컴파일러에게 "이 값은 절대 null이 아니다"라고 단언하는 것인데, 단언이 틀려 값이 실제로 `null`이면 런타임에 `NullPointerException`이 발생해 앱이 크래시합니다.

이는 Kotlin이 타입 안정성으로 없애려던 NPE를 다시 불러오는 셈입니다. 그래서 `!!`를 여기저기 쓰는 것은 흔히 코드 스멜로 간주되며, 로직이나 상태 관리를 개선해야 한다는 신호입니다. 대부분의 경우 스마트 캐스트(`if (x != null)`)나 `?.`·`?:`로 대체할 수 있습니다.

</def>
<def title="Q) 플랫폼 타입이 무엇이고, 왜 Kotlin에서도 NPE가 날 수 있나요?">

Java의 타입 시스템에는 null 안정성이 없어서, Java 메서드가 반환하는 값이 `null`일 수 있는지 Kotlin이 알 수 없습니다. 이 모호함을 처리하려고 Kotlin은 nullability를 알 수 없는 타입을 **플랫폼 타입**으로 취급하며, IDE에서 `String!`처럼 느낌표로 표시합니다.

플랫폼 타입은 nullable로 다룰지 non-nullable로 다룰지 개발자가 선택하는 "유연한" 타입입니다. 문제는 이를 non-nullable로 취급했는데 Java가 실제로 `null`을 반환하면 런타임 NPE가 난다는 점입니다. 따라서 `@Nullable` / `@NonNull` 어노테이션이 붙어 있지 않은 한, Java에서 오는 값은 nullable로 취급해 방어하는 것이 안전합니다.

</def>
</deflist>
