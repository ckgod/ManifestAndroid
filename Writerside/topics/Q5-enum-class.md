# Q5) enum class는 언제 사용하나요?

`enum class`는 **고정되고 서로 관련된 상수 집합**을 정의하기 위한 특수한 클래스입니다. 요일, 색상, 화면 상태처럼 "가능한 값이 미리 다 정해져 있는" 대상을 다룰 때 씁니다. 각 상수는 그 자체로 하나의 **싱글톤 인스턴스**이며, 쉼표로 구분해 선언합니다.

```kotlin
enum class Color {
    RED, GREEN, BLUE
}
```

`Color`는 `RED`, `GREEN`, `BLUE` 세 가지 값만 가질 수 있습니다. 문자열 `"RED"`나 정수 `0`으로 상태를 표현하는 것과 비교하면, 컴파일러가 잘못된 값을 애초에 막아 준다는 점이 다릅니다.

> **상수를 왜 타입으로 만드나** — `String`이나 `Int`로 상태를 표현하면 오타(`"REDD"`)나 범위를 벗어난 값(`5`)을 컴파일러가 잡아 주지 못하고, 결국 런타임에서 터집니다. enum은 값의 집합 자체를 타입으로 승격시켜, 잘못된 값이 코드에 들어오는 경로를 컴파일 시점에 차단합니다.

## 프로퍼티와 메서드 추가하기 {#properties}

enum 상수는 단순한 이름표에 그치지 않습니다. 주 생성자에 프로퍼티를 정의하고 각 상수에서 값을 넘겨줄 수 있으며, 클래스 본문에 메서드도 둘 수 있습니다.

```kotlin
enum class Direction(val degrees: Int) {
    NORTH(0),
    EAST(90),
    SOUTH(180),
    WEST(270);

    fun description(): String {
        return "Direction $name is $degrees degrees from North."
    }
}
```

```kotlin
val direction = Direction.NORTH
println(direction.description())   // Direction NORTH is 0 degrees from North.
```

상수 목록 뒤에 세미콜론(`;`)이 붙는 점에 주의하세요. 상수 선언과 클래스 본문을 구분하는 표시로, 본문에 무언가를 추가할 때만 필요합니다.

## when 표현식과 완전성 {#when}

컴파일러는 enum의 상수 전부를 알고 있습니다. 그래서 `when`에서 모든 케이스를 다뤘는지 **컴파일 시점에 검사**할 수 있고, 다 채웠다면 `else` 없이도 표현식으로 쓸 수 있습니다.

```kotlin
fun handleDirection(direction: Direction): String {
    return when (direction) {
        Direction.NORTH -> "You are heading North."
        Direction.EAST -> "You are heading East."
        Direction.SOUTH -> "You are heading South."
        Direction.WEST -> "You are heading West."
    }
}
```

여기에 상수를 하나 더 추가하면 이 `when`은 컴파일 에러가 나며 빠뜨린 케이스를 알려 줍니다. 값을 늘렸을 때 처리 누락을 컴파일러가 대신 찾아 주는 것 — 이것이 enum을 쓰는 실질적인 이득입니다.

## 기본 제공 프로퍼티와 메서드 {#builtin}

Kotlin은 모든 enum class에 다음을 기본으로 제공합니다.

| 멤버 | 반환 | 설명 |
|---|---|---|
| `name` | `String` | enum 상수의 이름 |
| `ordinal` | `Int` | 선언 순서(0부터 시작) |
| `values()` | `Array<E>` | 모든 상수의 배열 |
| `valueOf(String)` | `E` | 이름으로 상수를 찾음 |
| `entries` | `List<E>` | 모든 상수의 리스트(Kotlin 1.9+) |

```kotlin
val colors = Color.values()
println(colors.joinToString())   // RED, GREEN, BLUE

val color = Color.valueOf("RED")
println(color.ordinal)           // 0
```

`ordinal`은 편해 보이지만 **선언 순서에 의존**한다는 점을 기억해야 합니다. 나중에 상수 순서를 바꾸면 저장해 둔 `ordinal` 값이 조용히 다른 상수를 가리키게 됩니다. 직렬화나 DB 저장에는 `ordinal` 대신 `name`을 쓰는 편이 안전합니다.

## 사용 사례 {#use-cases}

1. **상태 표현** — `LOADING`, `SUCCESS`, `ERROR`처럼 화면·요청의 유한한 상태
2. **고정된 옵션 정의** — `ADMIN`, `EDITOR`, `VIEWER` 같은 사용자 역할
3. **제어 흐름 단순화** — `when`과 결합해 분기를 명시적으로 표현

## Pro Tips {#pro-tips}

### values() 대신 entries {#entries}

`values()`는 호출할 때마다 **새 배열을 만들어 반환**합니다. 배열은 가변이라 호출자가 내용을 바꿔 버릴 수 있고, 이를 막으려면 매번 복사본을 넘겨야 하기 때문입니다. 반복문 안에서 `values()`를 호출하면 그만큼 배열이 계속 생성됩니다.

Kotlin 1.9에서 도입된 `entries` 프로퍼티는 불변 `List<E>`를 **미리 만들어 두고 재사용**합니다. 매번 새로 할당하지 않으므로 성능과 메모리에서 유리하고, 리스트라 컬렉션 연산도 자연스럽게 이어집니다.

```kotlin
for (value in MyEnum.entries) {
    println(value)
}
```

`entries`는 하위 호환을 위해 `values()`와 공존하므로 점진적으로 옮겨 가면 됩니다. 새로 쓰는 코드라면 `entries`가 기본 선택입니다.

### 제네릭 values()와 valueOf() 제안 {#generic-values}

현재 `values()`와 `valueOf()`는 `static`이라 `Color.values()`처럼 **enum 타입을 명시적으로 지목해야** 호출할 수 있습니다. 타입을 컴파일 시점에 모르는 제네릭 코드에서는 결국 리플렉션에 의존해야 했습니다.

[KEEP 제안서](https://github.com/Kotlin/KEEP/blob/master/proposals/generic-values-and-valueof-for-enums.md)는 이를 제네릭 메서드로 확장하는 방향을 다룹니다. `values<T>()`와 `valueOf<T>(String)`로 enum 타입을 타입 인자로 받아, 리플렉션 없이 타입 안전하게 처리하자는 것입니다.

이 방식의 이점은 세 가지로 정리됩니다. 제네릭 경로에서도 타입이 강제되므로 **타입 안전성**이 올라가고, enum을 다루는 라이브러리가 특정 타입을 하드코딩할 필요가 없어 **API 설계가 단순**해지며, 보일러플레이트가 줄어 **가독성**이 개선됩니다. 기존 `values()`·`valueOf()` 사용법은 그대로 유지되고 제네릭 버전이 별도로 추가되는 형태라 하위 호환도 유지됩니다.

### sealed class와의 차이 {#vs-sealed}

3주차에서 다룬 `sealed class`와 enum은 둘 다 `when` 완전성 검사를 제공한다는 점에서 겹칩니다. 갈리는 지점은 **서브타입이 각자 다른 데이터를 가질 수 있는가**입니다.

| | `enum class` | `sealed class` |
|---|---|---|
| 각 항목의 정체 | 같은 타입의 인스턴스(상수) | 서로 다른 타입의 서브클래스 |
| 항목별 고유 데이터 | 불가(구조가 동일) | 가능(서브타입마다 자유) |
| 서브타입 형태 | 상수만 | `object`·`data class`·일반 class |
| `when` 완전성 | 지원 | 지원 |
| 적합한 대상 | 고정된 값의 열거 | 복잡한 계층·다형적 상태 |

결제 수단처럼 **항목마다 들고 다니는 데이터가 다르면** sealed class가 맞습니다.

```kotlin
sealed class Payment {
    object Cash : Payment()
    data class CreditCard(val cardNumber: String) : Payment()
    data class PayPal(val email: String) : Payment()
}

fun processPayment(payment: Payment) = when (payment) {
    is Payment.Cash -> println("Paying with cash")
    is Payment.CreditCard -> println("Paying with card: ${payment.cardNumber}")
    is Payment.PayPal -> println("Paying via PayPal: ${payment.email}")
}
```

반대로 방위처럼 **구조가 같고 값만 다르면** enum이 더 가볍고 명확합니다.

```kotlin
enum class Direction(val degrees: Int) {
    NORTH(0), EAST(90), SOUTH(180), WEST(270);

    fun describe() = "Direction $name with $degrees degrees."
}
```

실무에서는 네트워크 응답이나 UI 상태처럼 상태마다 담을 데이터가 다른 경우 sealed class를, 방향·요일·역할처럼 값의 목록이 고정된 경우 enum을 고릅니다.

## 요약 {#summary}

> **TL;DR** — `enum class`는 가능한 값이 미리 정해진 상수 집합을 타입으로 승격시킵니다. 각 상수는 싱글톤이고, 주 생성자 프로퍼티와 메서드를 가질 수 있으며, `when`에서 완전성 검사를 받아 케이스 누락을 컴파일 시점에 잡습니다. 항목마다 서로 다른 데이터를 담아야 하면 enum이 아니라 sealed class를 쓰세요.

1. **고정된 상수 집합**: 각 상수는 싱글톤 인스턴스. 잘못된 값이 들어올 경로를 컴파일러가 차단.
2. **프로퍼티·메서드 보유**: 주 생성자로 값을 받고 본문에 메서드 정의 가능(상수 목록 뒤 `;` 필요).
3. **`when` 완전성**: 모든 케이스를 다루면 `else` 불필요. 상수 추가 시 누락을 컴파일 에러로 알려 줌.
4. **기본 멤버**: `name`, `ordinal`, `values()`, `valueOf()`, 그리고 1.9의 `entries`. 저장·직렬화엔 `ordinal`보다 `name`.
5. **`entries` 선호**: `values()`는 호출마다 새 배열을 만들지만 `entries`는 불변 리스트를 재사용.
6. **sealed와의 선택**: 항목별 고유 데이터가 필요하면 sealed class, 값의 열거면 enum.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) enum class는 언제 사용하나요?">

가능한 값이 미리 고정되어 있고 서로 관련된 상수 집합을 표현할 때 사용합니다. 화면·요청 상태(`LOADING`/`SUCCESS`/`ERROR`), 사용자 역할(`ADMIN`/`EDITOR`/`VIEWER`), 방향·요일처럼 값의 목록이 정해진 대상이 대표적입니다. 값의 집합 자체를 타입으로 만들어 잘못된 값이 들어오는 것을 컴파일 시점에 막고, `when`과 결합해 분기 누락까지 컴파일러가 잡아 줍니다.

</def>
<def title="Q) enum class가 when에서 else 없이 컴파일되는 이유는?">

컴파일러가 해당 enum의 상수 전부를 알고 있어 완전성(exhaustiveness) 검사를 할 수 있기 때문입니다. 모든 상수를 다뤘다면 도달할 수 없는 케이스가 없으므로 `else`가 필요 없습니다. 나중에 상수를 추가하면 그 `when`은 컴파일 에러가 나면서 빠진 케이스를 알려 주므로, 값이 늘어났을 때의 처리 누락을 런타임이 아닌 컴파일 시점에 발견할 수 있습니다.

</def>
<def title="Q) values() 대신 entries를 쓰라는 이유는?">

`values()`는 호출될 때마다 새 배열을 생성해 반환합니다. 배열이 가변이라 호출자가 내용을 변경할 수 있어, 이를 막으려면 매번 복사본을 만들어야 하기 때문입니다. 반복문에서 호출하면 그만큼 할당이 반복됩니다. Kotlin 1.9의 `entries`는 불변 `List<E>`를 미리 만들어 두고 재사용하므로 할당이 없고, 리스트라 컬렉션 연산으로 자연스럽게 이어집니다. 하위 호환을 위해 둘은 공존하므로 점진적 전환이 가능합니다.

</def>
<def title="Q) ordinal을 저장 값으로 쓰면 안 되는 이유는?">

`ordinal`은 선언 순서를 그대로 반환하는 값이라, 나중에 상수 순서를 바꾸거나 중간에 새 상수를 끼워 넣으면 의미가 달라집니다. DB나 파일에 `ordinal`을 저장해 둔 상태에서 순서가 바뀌면, 저장된 숫자가 조용히 다른 상수를 가리키게 되고 컴파일러는 이를 알려 주지 못합니다. 직렬화·영속화에는 순서에 영향받지 않는 `name`을 사용하는 편이 안전합니다.

</def>
<def title="Q) enum class와 sealed class는 어떻게 구분해서 쓰나요?">

핵심 기준은 항목마다 서로 다른 데이터를 가져야 하는가입니다. enum의 상수는 모두 같은 타입의 인스턴스라 구조가 동일하고, 프로퍼티를 두더라도 모든 상수가 같은 프로퍼티를 갖습니다. sealed class는 서브타입을 `object`·`data class`·일반 클래스로 자유롭게 정의할 수 있어 항목별로 고유한 프로퍼티와 동작을 가질 수 있습니다. 따라서 네트워크 응답이나 UI 상태처럼 상태별 데이터가 다르면 sealed class를, 방향·요일·역할처럼 값의 목록이 고정되어 있으면 enum을 씁니다. 두 경우 모두 `when` 완전성 검사는 동일하게 제공됩니다.

</def>
</deflist>
