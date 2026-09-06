# Q19) 함수형(SAM) 인터페이스와 SAM 변환

**추상 메서드가 정확히 하나뿐인 인터페이스**를 함수형 인터페이스, 또는 SAM(Single Abstract Method) 인터페이스라고 합니다. 메서드가 하나뿐이라는 건, 그 인터페이스가 사실상 **함수 하나에 대한 계약**과 다르지 않다는 뜻입니다. `run(): Unit` 하나만 가진 `Runnable`은 구조적으로 `() -> Unit`과 같습니다.

Q18에서 람다는 `FunctionN` 객체로 컴파일된다고 했습니다. SAM 변환은 그 람다를 `FunctionN` 대신 **원하는 인터페이스의 구현체로** 바꿔 주는 장치입니다. 덕분에 인터페이스를 구현하는 무거운 코드를 쓰지 않고 람다 하나로 끝낼 수 있습니다.

## fun interface {#fun-interface}

코틀린에서 함수형 인터페이스는 `interface` 앞에 `fun`을 붙여 선언합니다.

```kotlin
fun interface Greeter {
    fun greet(name: String): String
}

// 람다로 바로 구현
val greeter = Greeter { name -> "Hello, $name!" }
println(greeter.greet("Kotlin")) // Hello, Kotlin!
```

`Greeter { ... }`가 되는 이유가 SAM 변환입니다. `greet`가 유일한 추상 메서드이므로, 컴파일러는 람다 `{ name -> ... }`를 그 메서드의 구현으로 받아들입니다.

`fun`을 붙이지 않은 일반 인터페이스로 같은 걸 하려면 익명 객체를 직접 써야 합니다.

```kotlin
interface PlainGreeter {           // fun 없음
    fun greet(name: String): String
}

// 람다로는 안 된다 — 익명 객체를 써야 한다
val greeter = object : PlainGreeter {
    override fun greet(name: String) = "Hello, $name!"
}
```

즉 **코틀린에서 SAM 변환을 받으려면 `fun interface`로 선언해야** 합니다(뒤 [fun 키워드를 요구하는 이유](#why-fun) 참고).

멤버 제약은 두 갈래입니다. 추상 메서드는 하나여야 하지만, **비추상**(기본 구현) 메서드와 프로퍼티, `companion object`는 얼마든 가질 수 있습니다. 반면 **추상 프로퍼티는 가질 수 없습니다.**

```kotlin
fun interface Bad {
    fun act(x: Int)
    val name: String   // error: functional interface cannot have abstract properties.
}
```

람다는 메서드 하나의 구현일 뿐이라 프로퍼티까지 채워 줄 수 없기 때문입니다.

이미 있는 함수가 시그니처에 맞는다면 람다 대신 [메서드 참조](Q18-lambda.md#method-reference)를 넘겨도 됩니다.

```kotlin
fun buildGreeting(name: String) = "Hello, $name!"

val greeter = Greeter(::buildGreeting)
```

## SAM 변환의 동작 {#sam-conversion}

SAM 변환은 **람다를 함수형 인터페이스의 구현 객체로 자동 변환**하는 컴파일러 동작입니다. 없다면 우리가 직접 익명 객체를 만들어야 하는 것을, 컴파일러가 대신 해 줍니다.

```kotlin
// SAM 변환 (우리가 쓰는 코드)
executor.execute { println("Task running") }

// 의미상 이것과 동등하다 (실제 코드 생성 방식은 아래 Java 상호운용 절 참고)
executor.execute(object : Runnable {
    override fun run() { println("Task running") }
})
```

핵심은 **문법이 같다는 것**입니다. Q18에서 본 것과 똑같은 `{ ... }` 람다인데, 넘기는 자리가 함수형 인터페이스를 기대하면 `FunctionN` 대신 그 인터페이스의 구현체로 컴파일됩니다. 어느 쪽이 될지는 **받는 쪽의 타입**이 결정합니다.

제약 하나 — SAM 변환은 **인터페이스에만** 적용됩니다. 추상 메서드가 하나뿐이더라도 추상 클래스는 대상이 아니라, 여전히 `object : SomeAbstractClass { ... }`로 써야 합니다.

## Java 상호운용 {#java-interop}

SAM 변환이 태어난 진짜 이유는 Java 생태계와의 마찰을 없애는 것입니다.

Java 8에서 람다가 들어오기 전에는, 메서드에 "동작"을 넘기는 유일한 방법이 익명 내부 클래스였습니다. 한 줄을 실행하려고 아래처럼 써야 했습니다.

```java
// Java 8 이전
executor.execute(new Runnable() {
    @Override
    public void run() {
        System.out.println("Task is running.");
    }
});
```

개발자의 의도는 "이 한 줄을 실행해"인데, 클래스 인스턴스화와 메서드 오버라이드라는 의례가 그 의도를 가립니다. `Runnable`, `Callable`, `Comparator`, 그리고 안드로이드의 수많은 리스너(`OnClickListener`, `OnLongClickListener` 등)가 전부 이런 SAM 인터페이스입니다.

코틀린은 "더 나은 Java", 즉 이 방대한 Java 라이브러리 생태계와 자연스럽게 맞물리는 것을 목표로 했습니다. 그래서 **Java의 SAM 인터페이스를 기대하는 자리에는 람다를 그냥 넘길 수 있게** 했고, 나머지 변환은 컴파일러가 떠안습니다.

```kotlin
// 안드로이드에서 흔히 보는 코드 — setOnClickListener는 Java SAM 인터페이스를 받는다
button.setOnClickListener { view -> handleClick(view) }
```

즉 함수형 언어와 레거시 객체지향 API 사이의 임피던스 불일치를 개발자 대신 컴파일러가 처리하는 것입니다. 코드는 관용적인 코틀린으로 유지되면서 바이트코드는 Java와 완벽히 호환됩니다.

다만 그 "변환"이 익명 클래스 생성이라고 생각하면 옛 정보입니다. 현재 컴파일러는 SAM 변환에도 `invokedynamic`을 써서 JVM의 `LambdaMetafactory`가 런타임에 구현체를 만들게 합니다. **안드로이드는 예외**입니다 — `LambdaMetafactory`가 안드로이드 런타임에 없어 D8이 빌드 시점에 다시 synthetic 클래스로 되돌리고, 크래시 스택 트레이스에 찍히는 `$$ExternalSyntheticLambda`가 그 결과물입니다. 자세한 내용은 [Q15의 안드로이드 desugaring](Q15-higher-order-function.md#android-desugaring)에 있습니다.

## fun 키워드를 요구하는 이유 {#why-fun}

Java 인터페이스는 SAM이기만 하면 코틀린에서 자동으로 SAM 변환이 됩니다. 그런데 **코틀린이 정의한 인터페이스는 `fun`을 붙여야만** 됩니다. 왜 자동으로 안 해 줄까요.

메서드가 하나인 코틀린 인터페이스라고 해서 다 "함수처럼 쓰라고 만든 것"은 아닙니다. 단순히 지금 추상 메서드가 하나일 뿐, 나중에 더 늘어날 수도 있고, 계약(contract)으로서 이름과 타입에 의미를 담은 것일 수도 있습니다. 여기에 컴파일러가 마음대로 SAM 변환을 열어 주면 설계 의도와 어긋날 수 있습니다.

그래서 코틀린은 **`fun` 키워드로 명시적 opt-in**을 요구합니다. `fun interface`라고 적었다는 건 "이건 함수 하나를 뜻하니 람다로 받아도 좋다"는 설계자의 선언입니다. Java 인터페이스는 코틀린이 손댈 수 없는 남의 코드라 상호운용을 위해 자동으로 열어 주고, 내 코드에서는 의도를 분명히 밝히게 한 것입니다.

## 함수 타입 vs fun interface {#vs-function-type}

메서드 하나짜리라면 그냥 함수 타입(`(String) -> String`)을 쓰면 되지, 왜 굳이 `fun interface`를 만들까요. 둘 다 람다로 넘길 수 있으니 겹칩니다. 기준은 이렇습니다.

**함수 타입이 나은 경우** — 그저 "함수 하나를 넘긴다"가 전부일 때. 가볍고 별도 선언이 필요 없습니다.

```kotlin
fun onEach(action: (String) -> Unit) { ... }
```

**`fun interface`가 나은 경우**:

- **이름이 의미를 담을 때** — `fun interface RetryPolicy { fun shouldRetry(attempt: Int): Boolean }`는 `(Int) -> Boolean`보다 무엇을 넘기는지 분명합니다.
- **타입으로 구분해야 할 때** — 함수 타입 `(Int) -> Unit` 둘은 같은 타입이라 오버로드로 구분할 수 없지만, 서로 다른 `fun interface`는 별개 타입이라 구분됩니다.
- **추가 멤버가 필요할 때** — `fun interface`는 추상 메서드 하나 외에 기본 구현 메서드나 **비추상** 프로퍼티, `companion object`를 가질 수 있습니다(추상 프로퍼티는 불가). 함수 타입은 그럴 수 없습니다.

정리하면, 순수하게 함수만 넘기면 함수 타입이 간결하고, 이름·타입 구분·부가 멤버 중 하나라도 필요하면 `fun interface`가 맞습니다.

## 요약 {#summary}

> **TL;DR** — 추상 메서드가 하나뿐인 인터페이스가 함수형(SAM) 인터페이스입니다. 그 자리에 람다를 넘기면 컴파일러가 인터페이스 구현 객체로 바꿔 줍니다(SAM 변환). Java 인터페이스는 자동으로, 코틀린 인터페이스는 `fun interface`로 선언해야 됩니다.

1. **정의**: 추상 메서드가 정확히 하나인 인터페이스. 사실상 함수 하나에 대한 계약.
2. **SAM 변환**: 람다를 그 인터페이스의 구현체로 자동 변환. 익명 객체를 손으로 안 써도 된다. 어느 타입이 될지는 받는 쪽이 결정한다. **인터페이스에만** 적용되고 추상 클래스는 대상이 아니다.
3. **`fun interface`**: 코틀린에서 SAM 변환을 받으려면 필요한 선언. 추상 메서드는 하나, 비추상 멤버는 여럿 가능하되 **추상 프로퍼티는 불가**.
4. **Java 상호운용**: `Runnable`·`Comparator`·안드로이드 리스너 등 Java SAM 인터페이스에 람다를 그냥 넘길 수 있다. 이게 SAM 변환의 본래 목적. 코드 생성은 익명 클래스가 아니라 `invokedynamic`이며, 안드로이드에서만 D8이 다시 클래스로 되돌린다(Q15).
5. **왜 `fun`이 필요한가**: Java 인터페이스는 남의 코드라 자동 허용, 코틀린 인터페이스는 설계 의도를 명시적으로 밝히게 opt-in.
6. **vs 함수 타입**: 순수 함수 전달이면 함수 타입, 이름·타입 구분·부가 멤버가 필요하면 `fun interface`.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 함수형(SAM) 인터페이스란 무엇인가요?">

추상 메서드가 정확히 하나인 인터페이스입니다. 메서드가 하나뿐이라 사실상 함수 하나에 대한 계약과 같고, 그래서 익명 클래스를 구현하는 대신 람다 표현식이나 메서드 참조로 구현할 수 있습니다. 코틀린에서는 `interface` 앞에 `fun`을 붙여 선언합니다. `Runnable`, `Comparator`, 안드로이드의 각종 리스너가 대표적인 예입니다.

</def>
<def title="Q) SAM 변환이란 무엇인가요?">

람다를 함수형 인터페이스의 구현체로 컴파일러가 자동 변환하는 것입니다. 변환이 없다면 `object : Runnable { override fun run() { ... } }`처럼 익명 객체를 직접 써야 하지만, SAM 변환 덕분에 `{ ... }` 람다만 넘기면 됩니다. 문법은 Q18의 일반 람다와 똑같고, 넘기는 자리가 함수형 인터페이스를 기대하면 `FunctionN` 대신 그 인터페이스의 구현체로 컴파일됩니다. 다만 실제 코드 생성은 익명 클래스가 아니라 `invokedynamic` + `LambdaMetafactory`이며(안드로이드는 D8이 synthetic 클래스로 되돌림), SAM 변환은 인터페이스에만 적용되어 추상 클래스는 대상이 아닙니다.

</def>
<def title="Q) 코틀린 인터페이스는 왜 fun 키워드를 붙여야 SAM 변환이 되나요?">

Java 인터페이스는 코틀린이 수정할 수 없는 남의 코드이므로 상호운용을 위해 SAM 변환을 자동으로 열어 줍니다. 반면 코틀린이 정의한 인터페이스는, 지금 메서드가 하나라도 그것이 "함수로 쓰라"는 의도인지 컴파일러가 알 수 없습니다. 나중에 메서드가 늘 수도 있고 계약으로서 의미를 담은 것일 수도 있습니다. 그래서 `fun` 키워드로 "이건 함수 하나를 뜻하니 람다로 받아도 좋다"는 의도를 명시적으로 opt-in 하게 합니다.

</def>
<def title="Q) 함수 타입 대신 fun interface를 쓰는 이유는 무엇인가요?">

둘 다 람다로 넘길 수 있지만, 세 경우에 `fun interface`가 낫습니다. 첫째, 이름이 의미를 담을 때 — `(Int) -> Boolean`보다 `RetryPolicy.shouldRetry(attempt)`가 의도를 분명히 드러냅니다. 둘째, 타입으로 구분해야 할 때 — 같은 시그니처의 함수 타입은 하나의 타입이라 오버로드로 구분되지 않지만 서로 다른 `fun interface`는 별개 타입입니다. 셋째, 추상 메서드 외에 기본 구현 메서드나 비추상 프로퍼티, `companion object` 같은 부가 멤버가 필요할 때입니다(추상 프로퍼티는 `fun interface`에서도 금지입니다). 이런 요구가 없고 그저 함수를 넘기기만 하면 함수 타입이 더 간결합니다.

</def>
</deflist>
