# Q20) 확장과 그 장단점

확장(extension)은 **클래스의 소스를 건드리지 않고 기능을 덧붙이는** 방법입니다. 상속도 필요 없습니다. 손댈 수 없는 표준 라이브러리나 서드파티 클래스를 보강할 때 특히 쓸모가 있습니다.

```kotlin
fun Int.isEven(): Boolean = this % 2 == 0

println(4.isEven())   // true
```

`Int`를 수정하지 않았는데 모든 `Int`에서 `isEven()`을 부를 수 있습니다. 점 앞의 타입(`Int`)을 **수신 타입**, 함수 안의 `this`를 **수신 객체(receiver)**라고 부릅니다.

여기서 미리 못을 박아 둘 것이 하나 있습니다. "확장"이라는 말과 달리 확장은 클래스에 무언가를 **집어넣지 않습니다.** 멤버처럼 보이는 건 문법일 뿐이고 실제로는 바깥에 따로 있는 정적 함수입니다. 아래에 나오는 동작 대부분이 이 사실 하나에서 나옵니다.

## 확장 프로퍼티 {#extension-property}

프로퍼티도 같은 방식으로 붙일 수 있습니다.

```kotlin
val String.firstChar: Char
    get() = this[0]

println("Hello".firstChar)   // H
```

다만 **확장 프로퍼티는 값을 저장할 수 없습니다.** backing field가 없기 때문입니다. 초기값을 주려고 하면 컴파일 오류입니다.

```kotlin
val String.bad: Char = 'x'
// error: extension property cannot be initialized because it has no backing field.
```

클래스 바깥에 있는 함수가 그 클래스의 인스턴스마다 저장 공간을 새로 만들 수는 없으니 당연한 제약입니다. 즉 확장 프로퍼티는 **getter에 대한 문법적 편의**일 뿐, 상태를 갖지 않습니다. backing field의 기준 자체는 Q10에서 다룹니다.

`companion object`에도 확장을 붙일 수 있습니다.

```kotlin
val String.Companion.Empty: String
    get() = ""

createUser(name = String.Empty)   // createUser(name = "") 대신
```

## 컴파일 결과 — 정적 메서드 {#bytecode}

JVM에는 "확장 메서드"라는 개념이 없습니다. 그래서 컴파일러는 확장을 **파일 이름에 `Kt`를 붙인 클래스의 정적 메서드**로 만들고, **수신 객체를 첫 번째 파라미터로** 넘깁니다.

`StringExtensions.kt`에 확장을 정의하고 실제로 컴파일한 결과입니다.

```kotlin
// StringExtensions.kt
fun String.addExclamation(): String = this + "!"

val String.firstChar: Char
    get() = this[0]
```

```
$ javap -p StringExtensionsKt
public final class StringExtensionsKt {
  public static final java.lang.String addExclamation(java.lang.String);
  public static final char getFirstChar(java.lang.String);
}
```

`this`였던 수신 객체가 첫 파라미터로 내려왔고, 확장 프로퍼티는 정적 getter(`getFirstChar`)가 됐습니다. 여기서 따라오는 성질이 셋입니다.

- **런타임 비용이 없습니다.** 평범한 정적 메서드 호출 한 번이 전부입니다.
- **원본 클래스가 그대로입니다.** `String`의 바이트코드는 변하지 않습니다.
- **Java에서 호출할 수 있습니다.** `StringExtensionsKt.addExclamation("World")`처럼 정적 메서드로 부르면 됩니다.

## 확장의 해석 규칙 {#resolution}

확장이 "멤버가 아니라 정적 함수"라는 사실이 가장 크게 드러나는 곳이 **어느 함수가 불릴지 정하는 규칙**입니다. 면접에서 가장 자주 나오는 지점이기도 합니다.

### 정적 디스패치 {#static-dispatch}

멤버 함수는 런타임의 실제 타입을 보고 결정됩니다(동적 디스패치). 하지만 **확장 함수는 컴파일 시점의 선언 타입으로 결정됩니다.**

```kotlin
open class Base
class Derived : Base()

fun Base.name() = "Base 확장"
fun Derived.name() = "Derived 확장"

fun main() {
    val d: Base = Derived()   // 선언 타입 Base, 실제 타입 Derived
    println(d.name())
    println(Derived().name())
}
```

실행 결과입니다.

```
Base 확장
Derived 확장
```

실제 객체가 `Derived`인데도 `Base 확장`이 나옵니다. `d`의 **선언 타입이 `Base`**라서 컴파일 시점에 `Base.name()`으로 확정됐기 때문입니다. 정적 메서드로 컴파일된다는 점을 떠올리면 자연스럽습니다 — `name(d)`라는 호출이 이미 박혀 버린 것이고, 정적 메서드에는 오버라이드가 없습니다.

따라서 **확장으로는 다형성을 만들 수 없습니다.** 하위 타입마다 다르게 동작해야 한다면 확장이 아니라 멤버 함수로 선언하고 오버라이드해야 합니다.

### 멤버 함수 우선 {#member-wins}

멤버 함수와 확장 함수의 시그니처가 같으면 **언제나 멤버가 이깁니다.**

```kotlin
class Box { fun who() = "멤버" }
fun Box.who() = "확장"

println(Box().who())   // 멤버
```

확장이 기존 클래스의 동작을 조용히 바꿔치기하지 못하게 막는 안전장치입니다. 컴파일러도 경고로 알려 줍니다.

```
warning: this extension is shadowed by a member: 'fun who(): String' defined in 'Box'.
```

주의할 점은 이게 **라이브러리 업데이트 때 터질 수 있다**는 것입니다. 내가 확장으로 쓰던 이름이 다음 버전에서 멤버로 추가되면, 코드는 그대로인데 호출되는 구현이 조용히 바뀝니다.

## 접근 제약 {#limitations}

확장은 클래스 바깥의 정적 함수이므로, **그 클래스의 `private`·`protected` 멤버에 접근할 수 없습니다.**

```kotlin
class Box {
    private val secret = 1
}

fun Box.peek() = secret
// error: cannot access 'val secret: Int': it is private in 'Box'.
```

리플렉션에서도 마찬가지입니다. 확장은 원본 클래스의 바이트코드에 없으므로 그 클래스의 멤버로 조회되지 않습니다.

## nullable 수신 객체 {#nullable-receiver}

수신 타입을 nullable로 잡으면 **`null`인 대상에도 호출할 수 있는** 확장이 됩니다. 멤버 함수로는 불가능한 일입니다.

```kotlin
fun String?.orEmptyLike(): String = this ?: ""

val s: String? = null
println(s.orEmptyLike())   // "" (NPE 없음)
```

`this`가 `null`일 수 있으므로 함수 안에서 직접 처리해야 합니다. 표준 라이브러리의 `orEmpty()`, `isNullOrEmpty()`, `isNullOrBlank()`가 정확히 이 형태입니다.

## 장점과 단점 {#pros-cons}

**장점**

1. **가독성** — 유틸리티 함수를 `Util.process(x)` 대신 `x.process()`로 자연스럽게 읽히게 씁니다.
2. **모듈성** — 원본 클래스를 수정하거나 상속하지 않고 기능을 더합니다.
3. **재사용성** — 여러 곳에서 공유해 보일러플레이트를 줄입니다.

**단점**

1. **혼란** — 멤버 우선 규칙과 정적 디스패치는 직관과 어긋나는 방향이라, 모르면 잘못 예측하기 쉽습니다.
2. **남용에 따른 응집도 저하** — 무분별하게 붙이면 API가 비대해지고, 확장이 여러 파일·모듈에 흩어지면 코드 탐색이 어려워집니다.
3. **출처 추적의 어려움** — 확장은 임포트해야 보이므로, 큰 코드베이스에서는 이 함수가 어디서 왔는지 찾기 어렵습니다.

특히 라이브러리나 SDK를 만든다면 신중해야 합니다. 공개 확장은 그 라이브러리를 쓰는 모든 프로젝트의 전역 네임스페이스에 얹히기 때문입니다. 내부용이라면 가시성을 `internal`이나 `private`으로 좁혀 공개 API 표면을 깨끗하게 유지하는 편이 낫습니다.

## Pro Tips {#pro-tips}

### JvmSynthetic과 Java 노출 제어 {#jvm-synthetic}

확장이 정적 메서드로 컴파일된다는 건 **Java에서도 다 보인다**는 뜻입니다. Kotlin 전용 DSL처럼 Java에서 쓸 이유가 없는 API라면 오히려 방해가 됩니다.

`@JvmSynthetic`을 붙이면 생성된 메서드에 `ACC_SYNTHETIC` 플래그가 붙습니다.

```kotlin
@JvmSynthetic
fun String.hidden(): String = this + "!!!"
```

```
$ javap -v -p StringExtensionsKt
public static final java.lang.String hidden(java.lang.String);
  flags: (0x1019) ACC_PUBLIC, ACC_STATIC, ACC_FINAL, ACC_SYNTHETIC
```

이 플래그가 붙으면 **Java 컴파일러가 직접 호출을 거부**하고("cannot find symbol"), IDE 자동완성에서도 숨겨집니다. 다만 리플렉션으로는 여전히 접근 가능하므로 **보안 장치가 아니라 API 표면 정리 도구**로 이해해야 합니다. Kotlin 쪽에서는 아무 영향이 없습니다.

### internal 확장의 이름 맹글링 {#internal-mangling}

`internal`은 "같은 모듈 안에서만 접근"이라는 뜻인데, JVM에는 그런 가시성이 없습니다. 그래서 Kotlin은 이름 뒤에 모듈 이름을 붙여(맹글링) Java 쪽에서 실수로 쓰기 어렵게 만듭니다.

여기서 흔히 오해가 생깁니다. **이 맹글링은 클래스의 멤버에만 적용되고, 톱레벨 함수에는 적용되지 않습니다.** `-module-name myapp`으로 컴파일해 확인한 결과입니다.

```kotlin
class Holder {
    internal fun memberInternal() = "member internal"
}
internal fun topLevelInternal() = "top-level internal"
```

```
$ javap -p Holder
  public final java.lang.String memberInternal$myapp();   // 맹글링됨

$ javap -p MangleKt
  public static final java.lang.String topLevelInternal();  // 맹글링되지 않음
```

확장 함수는 언제나 톱레벨이므로 **`internal` 확장은 맹글링되지 않고 Java에서 평범한 이름의 `public static` 메서드로 보입니다.** Java 쪽에서까지 감추려면 `@JvmSynthetic`을 함께 붙여야 합니다.

```kotlin
@JvmSynthetic
internal fun String.hiddenInternal(): String = this + "(hidden)"
```

## 요약 {#summary}

> **TL;DR** — 확장은 클래스를 수정하지 않고 기능을 덧붙이는 문법으로, 수신 객체를 첫 파라미터로 받는 **정적 메서드**로 컴파일됩니다. 그래서 런타임 비용이 없는 대신 **정적 디스패치**(선언 타입으로 결정)이고, **멤버 함수가 항상 우선**하며, `private` 멤버에 접근할 수 없습니다.

1. **정체**: 소스 수정도 상속도 없이 기능을 더하는 문법. 클래스에 실제로 들어가지는 않는다.
2. **확장 프로퍼티**: backing field가 없어 값을 저장하지 못한다. getter에 대한 문법적 편의.
3. **컴파일 결과**: `파일이름Kt` 클래스의 `public static` 메서드. 수신 객체가 첫 파라미터. 런타임 오버헤드 없음, Java에서 호출 가능.
4. **정적 디스패치**: 런타임 타입이 아니라 **선언 타입**으로 결정된다. 확장으로는 다형성을 만들 수 없다.
5. **멤버 우선**: 시그니처가 같으면 멤버 함수가 이긴다. 컴파일러가 shadowed 경고를 낸다.
6. **접근 제약**: `private`·`protected` 멤버에 접근 불가. 리플렉션에서도 멤버로 안 잡힌다.
7. **nullable 수신 객체**: `String?`처럼 잡으면 `null`에도 호출 가능(`orEmpty` 계열).
8. **설계 주의**: 공개 확장은 전역 네임스페이스를 넓힌다. 내부용은 `internal`·`private`으로, Java에서도 감추려면 `@JvmSynthetic`.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 확장이란 무엇이며 어떤 장점이 있나요?">

클래스의 소스를 수정하거나 상속하지 않고 그 클래스에 함수나 프로퍼티를 덧붙이는 문법입니다. 표준 라이브러리나 서드파티 클래스처럼 손댈 수 없는 타입을 보강할 때 특히 유용합니다. 장점은 세 가지로, `Util.process(x)` 대신 `x.process()`로 읽히게 해 가독성이 좋아지고, 원본 클래스를 건드리지 않아 모듈성이 유지되며, 여러 곳에서 재사용해 보일러플레이트를 줄일 수 있습니다. 다만 클래스에 실제로 멤버가 추가되는 것은 아니고 겉보기 문법일 뿐입니다.

</def>
<def title="Q) 확장 함수는 어떻게 컴파일되나요?">

JVM에는 확장 메서드라는 개념이 없으므로, 컴파일러는 확장을 정의한 파일 이름에 `Kt`를 붙인 클래스(`StringExtensions.kt` → `StringExtensionsKt`)의 `public static` 메서드로 만들고 수신 객체를 첫 번째 파라미터로 전달합니다. 확장 프로퍼티는 정적 getter가 됩니다. 그 결과 평범한 정적 메서드 호출 한 번이므로 런타임 오버헤드가 없고, 원본 클래스의 바이트코드는 변하지 않으며, Java에서도 `StringExtensionsKt.addExclamation("World")`처럼 호출할 수 있습니다.

</def>
<def title="Q) 확장 함수는 왜 다형성이 동작하지 않나요?">

확장 함수가 정적으로 디스패치되기 때문입니다. 멤버 함수는 런타임의 실제 타입을 보고 결정되지만, 확장 함수는 컴파일 시점의 **선언 타입**으로 결정됩니다. `val d: Base = Derived()`에서 `d.name()`을 호출하면 실제 객체가 `Derived`여도 `Base`에 정의된 확장이 불립니다. 정적 메서드로 컴파일되어 호출이 컴파일 시점에 확정되고, 정적 메서드에는 오버라이드가 없기 때문입니다. 따라서 하위 타입마다 다르게 동작해야 한다면 확장이 아니라 멤버 함수로 선언하고 오버라이드해야 합니다.

</def>
<def title="Q) 멤버 함수와 확장 함수의 이름이 같으면 어떻게 되나요?">

항상 멤버 함수가 우선합니다. 확장이 기존 클래스의 동작을 조용히 바꿔치기하지 못하게 하는 안전장치이며, 컴파일러도 "this extension is shadowed by a member"라는 경고를 냅니다. 실무에서 주의할 점은 라이브러리 업데이트 시점입니다. 확장으로 쓰던 이름이 다음 버전에서 멤버로 추가되면 내 코드는 그대로인데 호출되는 구현이 조용히 바뀔 수 있습니다.

</def>
<def title="Q) 확장 프로퍼티에 값을 저장할 수 있나요?">

없습니다. 확장 프로퍼티에는 backing field가 없기 때문에 초기값을 주면 "extension property cannot be initialized because it has no backing field" 오류가 납니다. 확장은 클래스 바깥의 정적 함수라 인스턴스마다 저장 공간을 새로 만들 수 없기 때문입니다. 따라서 확장 프로퍼티는 상태를 갖지 못하는, getter에 대한 문법적 편의입니다.

</def>
<def title="Q) 확장의 단점과 설계 시 주의점은 무엇인가요?">

첫째, 멤버 우선 규칙과 정적 디스패치가 직관과 어긋나 동작을 잘못 예측하기 쉽습니다. 둘째, 남용하면 API가 비대해지고 확장이 여러 파일·모듈에 흩어져 코드 탐색과 유지 관리가 어려워집니다. 셋째, 확장은 임포트해야 보이므로 큰 코드베이스에서는 출처를 추적하기 어렵습니다. 특히 라이브러리나 SDK에서는 공개 확장이 사용자 프로젝트의 전역 네임스페이스에 그대로 얹히므로 신중해야 하며, 내부용이라면 `internal`이나 `private`으로 가시성을 좁히는 것이 좋습니다.

</def>
<def title="Q) @JvmSynthetic은 무엇에 쓰나요?">

확장 함수는 `public static` 메서드로 컴파일되어 Java에서도 그대로 보이는데, Kotlin 전용 DSL처럼 Java에서 쓸 이유가 없는 API라면 오히려 방해가 됩니다. `@JvmSynthetic`을 붙이면 생성된 메서드에 `ACC_SYNTHETIC` 플래그가 붙어 Java 컴파일러가 직접 호출을 거부하고 IDE 자동완성에서도 숨겨집니다. Kotlin 쪽 사용에는 영향이 없습니다. 다만 리플렉션으로는 여전히 접근할 수 있으므로 보안 장치가 아니라 API 표면을 정리하는 도구로 이해해야 합니다.

</def>
</deflist>
