# Q1) Any, Unit, Nothing 타입

Kotlin의 타입 시스템에는 숫자·문자열·컬렉션 같은 일상적인 타입 외에도, 타입 계층 자체의 **경계를 정의하는** 세 가지 특수 타입이 있습니다. 바로 `Any`, `Unit`, `Nothing`입니다.

이름만 보면 비슷해 보이지만 역할은 정반대에 가깝습니다. `Any`는 계층의 **꼭대기**를, `Nothing`은 **바닥**을, `Unit`은 "반환할 의미 있는 값이 없음"을 나타냅니다. 이 셋을 이해하면 Kotlin 타입 시스템이 어떻게 빈틈없이 닫혀 있는지, 그리고 왜 그렇게 설계됐는지가 보입니다.

## Any: 타입 계층의 루트 {#any}

Kotlin에서 선언하는 모든 클래스는 아무것도 명시하지 않아도 암시적으로 `Any`를 상속합니다. 즉 `Any`는 **모든 타입의 최상위 부모(root)** 이며, 개념적으로 Java의 `java.lang.Object`에 대응합니다.

모든 타입이 `Any`의 서브타입이므로, `Any` 타입 변수에는 `String`이든 `Int`든, 직접 만든 data class든, 심지어 람다까지 어떤 값이든 담을 수 있습니다.

```kotlin
fun printValue(value: Any) {
    println("The value is: $value")
}

printValue("Hello, Kotlin")     // The value is: Hello, Kotlin
printValue(123)                 // The value is: 123
printValue(User("skydoves"))    // The value is: User(name=skydoves)
```

`Any`는 모든 객체가 공통으로 갖는 세 가지 메서드 `equals()`, `hashCode()`, `toString()`을 정의합니다. 표준 라이브러리의 선언을 들여다보면 다음과 같습니다.

```kotlin
/**
 * Kotlin의 모든 클래스에 대해 궁극적인 부모 역할을 합니다.
 */
public open class Any {
    // 이 객체가 다른 객체와 의미적으로 "같은지" 확인한다
    public open operator fun equals(other: Any?): Boolean

    // 주로 HashMap 등에서 객체를 빠르게 저장·검색하는 데 쓰이는 정수를 반환한다
    public open fun hashCode(): Int

    // 객체의 간단한 텍스트 표현을 반환한다 (로깅·디버깅에 유용)
    public open fun toString(): String
}
```

한 가지 짚을 점은 nullable 버전인 `Any?`가 따로 있다는 것입니다. `Any`는 non-nullable 타입들의 최상위일 뿐이고, `null`까지 포함한 **모든 값의 진정한 최상위**는 `Any?`입니다. `Any?` 변수에는 어떤 값이든, 그리고 `null`도 담을 수 있습니다.

## Unit: 의미 있는 값의 부재 {#unit}

많은 언어에서 값을 반환하지 않는 함수는 `void`로 선언합니다. Kotlin에서 이 자리를 차지하는 것이 `Unit`입니다. 실행은 끝까지 완료하지만 **의미 있는 결과를 돌려주지 않는** 함수는 반환 타입이 `Unit`입니다.

```kotlin
fun showMessage(message: String): Unit {
    println(message)
}

// Unit 반환 타입은 생략할 수 있다 — 아래는 위와 완전히 동일하다
fun showMessageImplicit(message: String) {
    println(message)
}
```

Java의 `void`와 결정적으로 다른 점은, `Unit`이 **실제로 존재하는 타입**이며 값이 하나뿐인 싱글톤 `object`라는 것입니다. 이 차이는 특히 제네릭에서 실용적으로 드러납니다. 타입 매개변수 `T`를 받는 함수에 `Unit`을 타입 인자로 넘길 수 있는데, Java의 `void`로는 불가능한 일입니다.

```kotlin
interface Processor<T> {
    fun process(): T
}

class UnitProcessor : Processor<Unit> {
    // 명시적으로 아무것도 반환하지 않아도 암시적으로 Unit을 반환한다
    override fun process() {
        println("Processing complete, no value returned.")
    }
}
```

`Unit`의 내부는 이렇게 단 하나의 값만 갖는 `object`로 구현돼 있습니다.

```kotlin
/**
 * Unit 객체는 오직 하나의 값만 가진 타입이다. Java의 void 타입에 해당한다.
 */
public object Unit {
    override fun toString(): String = "kotlin.Unit"
}
```

결국 `Unit`은 "이 함수의 목적은 값을 돌려주는 게 아니라 **사이드 이펙트**(콘솔 출력, 변수 수정 등)를 수행하는 것"이라는 의미를 담습니다.

> **Compose와 Unit** — Jetpack Compose의 `@Composable` 함수는 대부분 반환 타입이 `Unit`입니다. UI와 관련된 값을 "반환"하는 대신, 내부 로직을 소비하면서 UI 트리를 **구축(방출)** 하는 것이 이들의 역할이기 때문입니다.

## Nothing: 절대 존재할 수 없는 값 {#nothing}

`Nothing`은 Kotlin 타입 시스템에서 가장 독특한 개념입니다. 한마디로 **"절대 존재할 수 없는 값"** 을 나타냅니다. 인스턴스가 아예 없기 때문에 `Nothing` 타입의 변수는 만들 수조차 없습니다.

주된 쓰임새는 코드가 **정상적으로 완료되지 않음**을 표현하는 것으로, 두 가지 맥락에서 나타납니다.

### 1. 절대 반환하지 않는 함수 {#never-returns}

항상 예외를 던지거나 무한 루프에 빠지는 함수는 반환 타입을 `Nothing`으로 둘 수 있습니다. 이는 컴파일러와 동료 개발자 모두에게 "이 함수 호출 뒤로는 실행이 이어지지 않는다"는 강한 신호가 됩니다.

```kotlin
fun fail(message: String): Nothing {
    throw IllegalArgumentException(message)
}

fun infiniteLoop(): Nothing {
    while (true) {
        // 이 루프는 절대 끝나지 않는다
    }
}
```

컴파일러는 `Nothing`을 반환하는 호출을 만나면 그 **바로 뒤의 코드를 도달 불가능(unreachable)** 으로 판단합니다. 덕분에 더 똑똑한 타입 추론과 흐름 분석이 가능해집니다.

### 2. 타입 계층의 최하위 {#bottom-type}

`Nothing`은 `Any`를 포함한 **다른 모든 타입의 서브타입**입니다. 즉 계층의 바닥(bottom type)입니다. 이 성질은 타입 추론에서 빛을 발합니다. 예를 들어 표준 라이브러리의 `emptyList()`는 `List<Nothing>`을 반환합니다.

```kotlin
val s: List<String> = emptyList()   // OK: List<Nothing> → List<String>

fun fail(): Nothing = throw IllegalStateException()

// throw는 Nothing 타입이므로, else 가지가 String 자리를 침범하지 않는다
val x: String = if (condition) "ok" else throw RuntimeException()
```

`List<Nothing>`은 요소를 하나도 담지 않음이 보장되므로 `List<String>`이든 `List<Int>`든 어떤 `List` 타입 변수에도 안전하게 대입됩니다. "그 타입의 요소만 담는다"는 약속을, 아무것도 담지 않음으로써 논리적으로 지키는 셈입니다.

내부 선언을 보면 `private` 생성자로 인스턴스 생성 자체를 막아 둔 것을 확인할 수 있습니다.

```kotlin
/**
 * Nothing은 인스턴스가 없다. "절대 존재하지 않는 값"을 나타낼 때 쓴다.
 * 함수의 반환 타입이 Nothing이면 절대 정상 반환하지 않음(항상 예외 등)을 의미한다.
 */
public class Nothing private constructor()
```

### Unit과 Nothing, 무엇이 다른가 {#unit-vs-nothing}

가장 자주 나오는 혼동이 "그냥 `Unit`을 쓰면 되지 않나?"입니다. 실제로 `throw`만 하는 함수의 반환 타입을 `Unit`으로 바꿔도 예외는 똑같이 던져지니, 언뜻 같아 보입니다. 하지만 두 타입이 컴파일러에게 전하는 **의미가 정반대**입니다.

| | `Unit` | `Nothing` |
|---|---|---|
| 값의 개수 | 정확히 1개 (`Unit` 싱글톤) | 0개 (인스턴스 없음) |
| 함수의 끝 | **정상적으로 반환한다** | **절대 정상 반환하지 않는다** |
| 호출 이후 코드 | 실행된다 (도달 가능) | 실행되지 않는다 (도달 불가능) |
| 타입 계층 위치 | 평범한 타입 (`Any`의 서브타입) | 최하위 — 모든 타입의 서브타입 |

한 문장으로 요약하면, **`Unit`은 "끝났지만 줄 값이 없다", `Nothing`은 "끝나지 않는다"** 입니다. 빈 상자를 돌려주는 것(`Unit`)과, 애초에 돌아오지 않는 것(`Nothing`)의 차이입니다.

```kotlin
// Unit: 정상적으로 반환한다 → 이후 코드로 제어가 넘어온다
fun logDone(): Unit {
    println("done")
}
fun useUnit() {
    logDone()
    println("이 줄은 실행된다")   // 도달 가능
}

// Nothing: 절대 반환하지 않는다 → 이후 코드로 제어가 넘어오지 않는다
fun fail(msg: String): Nothing {
    throw IllegalStateException(msg)
}
fun useNothing() {
    fail("boom")
    println("이 줄은 절대 실행되지 않는다")   // 컴파일러가 '도달 불가능'으로 인지
}
```

그럼 `Nothing`을 `Unit`으로 바꾸면 무엇이 깨질까요? 컴파일러가 두 가지 정보를 잃습니다.

**① 도달 불가능(reachability) 분석을 못 한다.**

```kotlin
fun getLength(text: String?): Int {
    if (text == null) fail("text is null")   // fail: Nothing
    return text.length                       // text가 non-null로 스마트 캐스트됨
}
```

`fail()`이 `Nothing`이라 컴파일러는 "여기를 지나면 `text`는 절대 null이 아니다"를 확신하고 스마트 캐스트를 해 줍니다. 만약 `fail()`이 `Unit`이었다면 컴파일러는 실행이 계속 이어진다고 보므로, 이 스마트 캐스트도 사라지고 아래처럼 "반환이 빠졌다"는 오류도 생깁니다.

```kotlin
fun demo(): Int {
    fail("x")   // fail: Nothing 이면 → 아래가 도달 불가능 → return 없어도 OK
}               // fail: Unit 이면 → 컴파일 오류: A 'return' expression required
```

**② 타입 추론에서 자리를 못 채운다.**

```kotlin
// Nothing은 String의 서브타입이므로 Elvis 식 전체가 String으로 추론된다 → OK
val name: String = user?.name ?: fail("no name")
```

`fail()`이 `Unit`이었다면 `user?.name`(`String`)과 `fail()`(`Unit`)의 공통 타입은 `Any`가 되어, `String` 자리에 대입하려는 순간 **타입 불일치** 컴파일 오류가 납니다. `throw`나 `return` 같은 표현식이 어떤 타입 자리에도 자연스럽게 들어갈 수 있는 것은 오직 `Nothing`이 **최하위 타입**이기 때문입니다.

정리하면, `Unit`으로도 예외는 던져지지만 컴파일러의 흐름 분석과 타입 추론이 무너집니다. "이 함수는 여기서 끝난다"는 사실을 타입으로 정확히 알려 주는 것이 `Nothing`의 존재 이유입니다.

## 요약 {#summary}

> **TL;DR** — `Any`, `Unit`, `Nothing`은 Kotlin 타입 계층의 뼈대를 정의합니다. `Any`는 모든 값을 담을 수 있는 최상위 타입(null 포함은 `Any?`), `Unit`은 반환할 의미 있는 값이 없음을 나타내는 싱글톤 타입, `Nothing`은 절대 존재할 수 없는 값이자 모든 타입의 최하위 타입으로 도달 불가능한 코드를 표현합니다.

1. **`Any`**: 모든 클래스의 암시적 루트(Java의 `Object`에 대응). `equals()`·`hashCode()`·`toString()`을 정의한다. `null`까지 포함한 진짜 최상위는 `Any?`다.
2. **`Unit`**: `void`에 해당하지만 값이 하나뿐인 실제 `object` 타입이다. 그래서 제네릭 타입 인자로 쓸 수 있고(`Processor<Unit>`), 함수가 사이드 이펙트만 수행함을 나타낸다.
3. **`Nothing`**: 인스턴스가 없는 타입. 항상 예외를 던지거나 무한 루프에 빠지는 함수의 반환 타입으로 쓰여, 그 뒤 코드를 도달 불가능으로 알린다.
4. **최하위 타입**: `Nothing`은 모든 타입의 서브타입이라, `throw`나 `emptyList()`(→ `List<Nothing>`)가 어떤 타입 자리에도 자연스럽게 들어맞는 근거가 된다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Any와 Any?의 차이는 무엇인가요?">

`Any`는 `null`이 아닌 모든 값의 최상위 타입이고, `Any?`는 거기에 `null`까지 포함한 전체 타입 시스템의 진정한 최상위 타입입니다. 따라서 `null`이 들어올 수 있는 값을 담으려면 `Any`가 아니라 `Any?`를 써야 합니다. `Any`는 Java의 `java.lang.Object`에 대응하며 `equals()`·`hashCode()`·`toString()`을 정의합니다.

</def>
<def title="Q) Unit은 Java의 void와 무엇이 다른가요?">

`void`는 "반환 값 없음"을 나타내는 키워드일 뿐 타입이 아니지만, `Unit`은 값이 단 하나뿐인 실제 싱글톤 `object` 타입입니다. 이 차이 때문에 `Unit`은 제네릭 타입 인자로 사용할 수 있습니다. 예를 들어 `Processor<T>`의 구현으로 `Processor<Unit>`을 만들 수 있지만, Java에서 `void`를 제네릭 인자로 넘기는 것은 불가능합니다.

</def>
<def title="Q) Nothing 타입은 언제, 왜 사용하나요?">

`Nothing`은 정상적으로 완료되지 않는 코드를 표현합니다. 항상 예외를 던지거나 무한 루프에 빠지는 함수의 반환 타입으로 지정하면, 컴파일러가 그 호출 이후의 코드를 도달 불가능으로 판단해 더 정확한 흐름 분석을 할 수 있습니다. 또한 `Nothing`은 모든 타입의 최하위(bottom) 타입이라, `val x: String = if (c) "ok" else throw ...`처럼 `throw` 표현식이 어떤 타입 자리에도 들어맞게 해 줍니다.

</def>
<def title="Q) Unit과 Nothing은 어떻게 다른가요? Nothing 대신 Unit을 쓰면 안 되나요?">

`Unit`은 함수가 **정상적으로 끝나되 돌려줄 값이 없음**을 나타내는, 값이 하나뿐인 타입입니다. 반면 `Nothing`은 함수가 **절대 정상적으로 끝나지 않음**(항상 예외를 던지거나 무한 루프)을 나타내는, 인스턴스가 아예 없는 최하위 타입입니다.

`throw`만 하는 함수의 반환 타입을 `Nothing` 대신 `Unit`으로 바꿔도 예외는 똑같이 던져지지만, 컴파일러가 두 가지 정보를 잃습니다. 첫째, 호출 이후 코드를 **도달 불가능**으로 인지하지 못해 스마트 캐스트가 사라지거나 "반환이 빠졌다"는 오류가 납니다. 둘째, `Nothing`이 최하위 타입이라 가능했던 타입 추론이 깨집니다. 예를 들어 `val x: String = a ?: fail()`은 `fail()`이 `Nothing`일 때만 컴파일되고, `Unit`이면 공통 타입이 `Any`가 되어 타입 불일치 오류가 납니다.

</def>
<def title="Q) emptyList()가 List<Nothing>을 반환하는 이유는 무엇인가요?">

`Nothing`이 모든 타입의 서브타입이므로 `List<Nothing>`은 공변성(covariance) 규칙상 `List<String>`, `List<Int>` 등 어떤 `List<T>`에도 안전하게 대입할 수 있습니다. 빈 리스트는 실제로 담긴 요소가 없어 "그 타입의 요소만 담는다"는 약속을 어길 일이 없으므로, 요소 타입을 `Nothing`으로 두는 것이 논리적으로 가장 정확합니다.

</def>
</deflist>
