# Q6) value class란 무엇인가요?

`value class`는 **단일 값을 감싸되 런타임에는 그 값 자체로 취급되는** 특수한 클래스입니다. 래퍼를 만들면 보통 객체 할당 비용이 따라오는데, value class는 컴파일 시점에 래퍼가 소거되어 기본 타입으로 대체됩니다. 타입 안전성은 얻고 할당 비용은 내지 않는 것이 목적입니다.

```kotlin
@JvmInline
value class Password(val value: String)

fun authenticate(password: Password) {
    println("Authenticating with password: ${password.value}")
}

val userPassword = Password("secure123")
authenticate(userPassword)
```

`Password`는 `String`을 감싸지만, 런타임에는 대체로 원시 `String`으로 표현됩니다. `Password` 객체를 위한 별도의 힙 할당이 발생하지 않습니다.

> **왜 필요한가** — `fun transfer(from: String, to: String)` 같은 시그니처는 인자 순서를 바꿔 넣어도 컴파일이 통과합니다. 둘 다 `String`이기 때문입니다. `UserId`와 `OrderId`가 모두 `Int`인 상황도 마찬가지입니다. value class는 같은 기본 타입의 서로 다른 쓰임을 별개의 타입으로 갈라놓아, 이런 실수를 컴파일 시점에 막습니다. 그러면서 성능은 원시 타입을 그대로 쓴 것과 같습니다.

## 이점 {#benefits}

1. **타입 안전성** — 둘 다 `Int`일 수 있는 `UserId`와 `OrderId`를 서로 다른 타입으로 구분합니다.
2. **성능 최적화** — 가능한 경우 기본 타입으로 컴파일되어 객체 할당을 피합니다.
3. **의미론적 명확성** — 값이 무엇을 뜻하는지 타입 이름으로 드러납니다.

## 제약 조건 {#constraints}

value class는 "경량 래퍼"라는 목적에 맞춰 강한 제약을 받습니다.

| 제약 | 내용 |
|---|---|
| 값을 저장하는 프로퍼티 | 주 생성자의 **읽기 전용 프로퍼티(`val`) 하나뿐** |
| 백킹 필드 | 그 외에 backing field를 갖는 프로퍼티는 선언 불가 |
| 상속 | 지원하지 않음(다른 클래스를 상속할 수도, 상속될 수도 없음. 인터페이스 구현은 가능) |
| 기반 타입 | `Nothing` 불가, 자기 자신을 기반 타입으로 둘 수 없음 |
| identity | 참조 동등성(`===`)이 제거됨 |

`identity` 항목이 특히 중요합니다. 래퍼가 런타임에 사라질 수 있다는 것은 **"이 객체"라고 부를 대상이 없을 수도 있다**는 뜻입니다. 그래서 value class에는 identity 개념이 성립하지 않고, `===` 비교가 컴파일 오류로 막힙니다. 컴파일러가 표현을 자유롭게 최적화할 수 있는 것도 이 제약 덕분입니다.

> **nullable은 제약이 아니다** — 기반 타입에 nullable을 쓰는 것 자체는 막히지 않습니다. `@JvmInline value class Name(val s: String?)`는 정상적으로 컴파일되고 `Name(null)`도 만들 수 있습니다. nullable을 쓰려면 `?`를 붙여야 한다는 것은 Kotlin 전체의 규칙이지 value class만의 제약이 아닙니다. 다만 nullable은 **박싱 여부**에 영향을 주는데, 이는 아래 Pro Tips에서 다룹니다.

### "프로퍼티가 하나뿐"의 정확한 의미 {#single-property}

여기서 "하나뿐"인 것은 **값을 저장하는** 프로퍼티입니다. 계산해서 돌려주는 프로퍼티는 개수 제한이 없습니다.

이유는 표현 방식에 있습니다. value class는 런타임에 기반 값 하나로 표현됩니다. `Person("ckgod")`가 사실상 `"ckgod"`라는 `String`이 되는 것이죠. 저장 공간이 그 하나뿐이니 상태를 더 담을 자리가 없습니다. 반면 `get()`은 저장이 아니라 호출할 때마다 기반 값에서 계산해내는 것이라 자리를 쓰지 않습니다.

```kotlin
@JvmInline
value class Person(val fullName: String) {
    val length: Int get() = fullName.length      // 계산 프로퍼티 — 가능
    val initial: Char get() = fullName.first()   // 여러 개 둬도 됨
    fun shout() = fullName.uppercase()           // 함수도 가능
}
```

반대로 값을 들고 있어야 하는 프로퍼티는 막힙니다.

```kotlin
@JvmInline
value class Bad(val s: String) {
    val cached: Int = s.length   // error: value class cannot have properties with backing fields.
    var counter: Int = 0         // 같은 이유로 불가
}
```

구분 기준은 단순합니다. `get()`으로 계산하면 통과하고, `=`로 초기값을 주는 순간 backing field가 필요해져 막힙니다. 그래서 value class는 단순 래퍼에 머물지 않고, 기반 값에서 파생되는 도메인 로직까지 담을 수 있습니다.

## 실제 사용 사례 {#use-cases}

Compose UI의 `KeyEvent`가 대표적인 예입니다. 플랫폼별 네이티브 키 이벤트를 감싸 타입을 부여하면서, 래퍼 비용은 지불하지 않습니다.

```kotlin
@kotlin.jvm.JvmInline
value class KeyEvent(val nativeKeyEvent: NativeKeyEvent)
```

키 입력은 프레임마다 대량으로 발생할 수 있는 이벤트라, 래퍼마다 힙 할당이 생기면 부담이 됩니다. value class는 그 지점에서 타입과 성능을 동시에 챙깁니다.

## Pro Tips {#pro-tips}

### inline class와 value class의 차이 {#inline-vs-value}

두 이름은 같은 기능의 서로 다른 세대를 가리킵니다. `inline class`는 Kotlin 1.3에서 실험적으로 도입되었고, Kotlin 1.5에서 `value class`가 안정화되면서 표준 용어로 대체되었습니다. `inline class`는 현재 deprecated입니다.

```kotlin
inline class InlineUserId(val value: Int)      // Kotlin 1.3, deprecated

@JvmInline
value class ValueUserId(val value: Int)        // Kotlin 1.5+, 표준
```

이름을 바꾼 이유는 **`inline` 함수와의 혼동** 때문입니다. 둘은 이름만 비슷할 뿐 다른 개념입니다.

1. inline class의 멤버 함수 자체는 인라인되지 않습니다.
2. non-local return 같은 inline 함수의 의미론적 이점을 제공하지 않습니다.
3. inline 함수는 컴파일러가 항상 인라인하지만, inline class는 **항상 인라인되지 않습니다**. 박싱이 필요한 상황이 존재합니다.

클래스에 붙는 `inline` 수정자가 실제로 하는 일은 객체 identity를 제거하고 제약을 부과하는 것이었고, 이는 "identity 없는 경량 값 추상화"라는 본래 의도에 `value`라는 이름이 더 잘 맞는다는 결론으로 이어졌습니다.

`@JvmInline` 어노테이션은 이 클래스가 JVM에서 고유한 컴파일 동작을 갖는다는 것을 명시합니다. 나아가 JVM에 값 타입을 도입하려는 [Project Valhalla](https://cr.openjdk.org/~briangoetz/valhalla/sov/01-background.html)가 완성되면, 어노테이션 없는 value class가 JVM 수준의 네이티브 값 타입 지원을 받을 수 있도록 미래 호환성을 열어 두려는 의도도 있습니다.

### 바이트코드로 보는 소거 {#bytecode}

"제로 코스트 추상화"가 실제로 어떻게 성립하는지는 디컴파일 결과에서 드러납니다.

```kotlin
@JvmInline
value class UserId(val id: String)

fun processId(userId: UserId) {
    println("Processing user with ID: ${userId.id}")
}

fun main() {
    val myId = UserId("user-123")
    processId(myId)
}
```

디컴파일하면 래퍼가 대부분의 자리에서 사라집니다.

```java
public final class IdKt {
    // 래퍼 클래스 자체는 리플렉션·박싱을 위해 바이트코드에 남는다
    public static final class UserId {
        private final String id;

        // 생성자와 getter는 synthetic이며 맹글링된다
        public static String constructor_impl(String id) {
            return id;
        }

        public static String getId_impl(UserId $this) {
            return $this.id;
        }
    }

    // 함수는 primitive 타입을 직접 받는다
    public static final void processId(String userId) {
        String var1 = "Processing user with ID: " + userId;
        System.out.println(var1);
    }

    public static final void main() {
        // 생성자 호출이 소거된다
        String myId = UserId.constructor_impl("user-123");
        processId(myId);
    }
}
```

세 가지가 눈에 띕니다.

1. **래퍼 소거** — Kotlin의 `fun processId(userId: UserId)`가 Java에서 `void processId(String userId)`가 되었습니다. `UserId` 타입이 `String`으로 대체되었습니다.
2. **힙 할당 없음** — `val myId = UserId("user-123")`는 `new UserId(...)`가 아니라 그냥 `String` 변수 대입이 됩니다. 런타임에 `UserId` 객체는 생성되지 않습니다.
3. **이름 맹글링** — 컴파일러가 `constructor_impl` 같은 맹글링된 static 헬퍼를 만듭니다. 내부용이라 직접 호출하지 않습니다.

다만 컴파일러가 래퍼를 소거할 수 **없는** 경우도 있습니다. 값이 객체로서 취급되어야 할 때, 즉 박싱이 필요할 때입니다.

```kotlin
val id1: Any = UserId("abc")                     // Any로 저장 → 박싱
val id2: UserId? = UserId("def")                 // nullable 타입으로 사용 → 박싱
val listOfIds = listOf(UserId("1"), UserId("2")) // 제네릭 컬렉션 → 박싱
```

두 번째 줄이 nullable과 관련된 지점입니다. `UserId`를 `String`으로 소거해 버리면 `null`이 "값이 없다"는 뜻인지 "`UserId`가 없다"는 뜻인지 구분할 수 없습니다. 그래서 `UserId?`처럼 **value class 타입 자체를 nullable로 쓰면** 래퍼를 살려 둡니다. 기반 타입까지 nullable인 경우(`value class Name(val s: String?)`)는 `Name(null)`과 `null`이 아예 겹치므로 박싱이 반드시 필요합니다.

이런 자리에서는 실제 `UserId` 객체가 힙에 만들어집니다. 객체 자체는 매우 가볍지만 할당 오버헤드는 피할 수 없습니다. 컴파일러는 언박싱된 표현과 박싱된 표현 사이를 필요에 따라 자동으로 오갑니다. 위 리스트에서 항목을 꺼내 `processId`에 넘기면, 호출 직전에 다시 `String`으로 언박싱됩니다.

정리하면 value class는 **"항상 공짜"가 아니라 "대개 공짜"** 입니다. 제네릭·nullable·`Any` 경계를 지날 때 박싱된다는 점을 알고 쓰면, 핫패스에서 어떤 시그니처를 택할지 판단할 수 있습니다.

### @JvmExposeBoxed — Java에서 쓰기 {#jvm-expose-boxed}

value class의 최적화는 Java 상호운용을 희생시킵니다. JVM에서 시그니처 충돌(`add(Int)`와 `add(PositiveInt)`가 둘 다 `add(int)`가 되는 문제)을 피하기 위해, 컴파일러가 함수 이름을 맹글링하기 때문입니다.

```kotlin
@JvmInline
value class PositiveInt(val number: Int) {
    init { require(number >= 0) }
}

fun PositiveInt.add(other: PositiveInt): PositiveInt =
    PositiveInt(this.number + other.number)
```

위 `add`는 `public static final int add-1bc5(int $this, int other)` 같은 시그니처로 컴파일됩니다. 이 이름은 Java에서 호출할 수도, 보이지도 않습니다. 게다가 생성자가 synthetic으로 컴파일되어 `new PositiveInt(5)` 자체가 불가능합니다. 결과적으로 value class는 Java 소비자에게 사실상 사용 불가능한 형태가 됩니다.

[@JvmExposeBoxed 제안서](https://github.com/Kotlin/KEEP/blob/jvm-expose-boxed/proposals/jvm-expose-boxed.md)는 이 문제를 옵트인 방식으로 해결합니다. 어노테이션을 붙이면 컴파일러가 맹글링되지 않은 **박싱 버전 API를 병렬로 추가 생성**합니다.

```kotlin
@JvmExposeBoxed
@JvmInline
value class PositiveInt(val number: Int) {
    init { require(number >= 0) }

    fun add(other: PositiveInt): PositiveInt =
        PositiveInt(this.number + other.number)
}
```

생성되는 박싱 메서드는 Java 세계와 Kotlin 세계를 잇는 브릿지로 동작합니다. 박싱된 인자를 받아 `unbox-impl`로 원시 값을 꺼내고, 기존의 맹글링된 최적화 함수를 호출한 뒤, 결과를 `box-impl`로 다시 감싸 Java 호출자에게 돌려줍니다.

얻는 것은 세 가지입니다. Java에서 `new PositiveInt(5)`와 `a.add(b)`를 자연스럽게 호출할 수 있고(**상호운용성**), Kotlin 코드는 여전히 언박싱 버전을 직접 호출하므로 **성능 손실이 없으며**(박싱 비용은 Java 호출 경계에서만 발생), 새로 생기는 public 생성자가 `init` 블록을 실행하므로 Java 쪽에서 음수 `PositiveInt`를 만드는 것을 막을 수 있습니다(**불변 조건 보호**).

어노테이션은 클래스 전체뿐 아니라 개별 함수·생성자에도 붙일 수 있어 노출 범위를 정밀하게 조절할 수 있고, 일괄 적용을 위한 `-Xjvm-expose-boxed` 컴파일러 플래그도 함께 제안되었습니다.

## 요약 {#summary}

> **TL;DR** — `value class`는 단일 `val` 하나를 감싸는 래퍼로, 컴파일 시점에 소거되어 런타임에는 기본 타입이 됩니다. 같은 기본 타입의 다른 쓰임(`UserId` vs `OrderId`)을 타입으로 구분하면서 힙 할당은 피합니다. 다만 `Any`·nullable·제네릭 경계에서는 박싱되므로 "항상 공짜"는 아닙니다. Kotlin 1.5부터 `inline class`를 대체했고 `@JvmInline`을 함께 붙입니다.

1. **정의**: 값을 저장하는 프로퍼티는 주 생성자의 `val` 하나뿐(계산 프로퍼티·함수는 자유). 상속 불가, `===` 사용 불가(identity 없음).
2. **목적**: 타입 안전성 확보 + 객체 할당 회피. 같은 primitive의 다른 의미를 갈라놓음.
3. **소거**: 함수 시그니처에서 래퍼가 사라지고 기본 타입이 직접 쓰임. `new` 호출 없음.
4. **박싱 예외**: `Any` 저장, nullable, 제네릭 컬렉션에 담길 때는 실제 객체가 생성됨.
5. **역사**: 1.3 `inline class`(실험) → 1.5 `value class`(안정) + `@JvmInline`. `inline` 함수와는 무관.
6. **Java 상호운용**: 맹글링·synthetic 생성자 때문에 Java에서 사실상 못 씀. `@JvmExposeBoxed`가 박싱 API를 병렬 생성해 해결.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) value class란 무엇이며 왜 사용하나요?">

단일 값을 감싸는 경량 래퍼로, 컴파일 시점에 래퍼가 소거되어 런타임에는 감싼 기본 타입으로 취급되는 클래스입니다. 목적은 두 가지를 동시에 얻는 것입니다. 첫째, 둘 다 `Int`인 `UserId`와 `OrderId`처럼 같은 기본 타입의 서로 다른 쓰임을 별개 타입으로 구분해 인자 혼동 같은 실수를 컴파일 시점에 막습니다. 둘째, 일반 래퍼 클래스와 달리 힙 할당이 발생하지 않아 성능 비용을 지불하지 않습니다.

</def>
<def title="Q) value class의 제약 조건은 무엇인가요?">

**값을 저장하는** 프로퍼티는 주 생성자의 읽기 전용 프로퍼티(`val`) 하나뿐입니다. 클래스 본문에는 `get()`으로 계산하는 프로퍼티와 함수를 얼마든지 둘 수 있고, `=`로 초기값을 주는 프로퍼티만 backing field가 필요해 막힙니다. 다른 클래스를 상속하거나 상속될 수 없으며(인터페이스 구현은 가능), 기반 타입으로 `Nothing`이나 자기 자신을 둘 수 없습니다. 또한 참조 동등성(`===`)이 제거되어 사용 시 컴파일 오류가 납니다. 래퍼가 런타임에 사라질 수 있으므로 "이 객체"라고 가리킬 identity 자체가 성립하지 않기 때문이며, 이 제약 덕분에 컴파일러가 표현을 자유롭게 최적화할 수 있습니다.

주의할 점은 **nullable은 제약이 아니라는 것**입니다. `value class Name(val s: String?)`는 정상적으로 컴파일되고 `Name(null)`도 만들 수 있습니다. nullable을 쓰려면 `?`를 붙여야 한다는 것은 Kotlin 전체의 규칙이지 value class만의 제한이 아닙니다. nullable이 실제로 영향을 주는 것은 허용 여부가 아니라 박싱 여부입니다.

</def>
<def title="Q) value class는 항상 힙 할당을 피하나요?">

아닙니다. 컴파일러가 래퍼를 소거할 수 없는 상황에서는 박싱이 일어나 실제 객체가 생성됩니다. 대표적으로 값을 `Any` 타입으로 저장할 때, nullable 타입(`UserId?`)으로 쓸 때, 제네릭 컬렉션(`List<UserId>`)에 담을 때입니다. 컴파일러는 언박싱된 표현과 박싱된 표현 사이를 자동으로 전환하므로, 리스트에서 꺼낸 값을 함수에 넘기면 호출 직전에 다시 언박싱됩니다. 즉 "항상 공짜"가 아니라 "대개 공짜"이며, 핫패스에서는 이 경계를 의식할 필요가 있습니다.

</def>
<def title="Q) inline class와 value class의 차이는 무엇인가요?">

기능적으로는 같고, 용어와 도입 시점이 다릅니다. `inline class`는 Kotlin 1.3에서 실험적으로 도입되었고, Kotlin 1.5에서 `value class`가 안정화되면서 표준 용어로 대체되어 현재 `inline class`는 deprecated입니다. 이름을 바꾼 이유는 `inline` 함수와의 혼동 때문입니다. inline class의 멤버 함수는 인라인되지 않고, non-local return 같은 inline 함수의 이점도 없으며, inline 함수와 달리 항상 인라인되지도 않습니다(박싱되는 경우가 있음). 클래스의 `inline` 수정자가 실제로 한 일은 identity 제거와 제약 부과였으므로, "identity 없는 경량 값"이라는 의도에 `value`가 더 맞는 이름이었습니다.

</def>
<def title="Q) @JvmInline 어노테이션은 왜 필요한가요?">

이 value class가 JVM에서 고유한 컴파일 동작(래퍼 소거, 언박싱 표현 사용)을 갖는다는 것을 명시적으로 표시합니다. 아울러 JVM에 값 타입을 도입하려는 Project Valhalla를 염두에 둔 장치이기도 합니다. Valhalla가 완성되면 어노테이션 없는 `value class`가 JVM 수준의 네이티브 값 타입 지원을 받을 수 있도록, 현재의 JVM 특화 동작을 어노테이션으로 구분해 미래 호환성을 확보해 둔 것입니다.

</def>
<def title="Q) value class를 Java에서 쓰기 어려운 이유와 해결책은?">

JVM에서 시그니처 충돌을 피하기 위해 컴파일러가 함수 이름을 맹글링하기 때문입니다(`add` → `add-1bc5`). 맹글링된 이름은 Java에서 호출할 수 없고 보이지도 않으며, 생성자도 synthetic으로 컴파일되어 `new PositiveInt(5)` 자체가 불가능합니다. 해결책은 `@JvmExposeBoxed` 어노테이션으로, 맹글링되지 않은 박싱 버전 API를 병렬로 생성하도록 컴파일러에 지시합니다. 이 박싱 메서드는 입력을 언박싱하고 기존 최적화 함수를 호출한 뒤 결과를 다시 박싱하는 브릿지로 동작하므로, Java 상호운용을 얻으면서 Kotlin 측 성능은 그대로 유지됩니다.

</def>
</deflist>
