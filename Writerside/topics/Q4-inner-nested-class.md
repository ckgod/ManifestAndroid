# Q4) inner class와 nested class의 차이

Kotlin에서는 클래스 안에 또 다른 클래스를 선언할 수 있습니다. 이때 **바깥 클래스 인스턴스와 어떤 관계를 맺느냐**에 따라 두 종류로 갈립니다. `inner` 키워드 없이 선언하면 **nested class**, `inner`를 붙이면 **inner class**입니다. 이 한 단어 차이가 메모리 동작까지 바꾸는 중요한 구분입니다.

> **Java와 정반대라 헷갈린다** — Java는 중첩 클래스가 **기본적으로 바깥 인스턴스를 참조(non-static)** 하고, `static`을 붙여야 분리됩니다. Kotlin은 **정반대로 기본이 분리(nested = static 상당)** 이고, `inner`를 붙여야 바깥을 참조합니다. Java에서 넘어온 사람이 가장 자주 걸려 넘어지는 지점입니다. Kotlin은 "더 안전한 쪽(분리)"을 기본값으로 둔 것입니다.

## 기본값: nested class {#nested}

`inner` 없이 선언한 중첩 클래스는 바깥 클래스 인스턴스에 대한 참조를 **가지지 않습니다**. Java의 `static` 중첩 클래스처럼 독립적인 존재라, 바깥 클래스의 프로퍼티나 함수에 (명시적으로 넘겨받지 않는 한) 접근할 수 없습니다.

```kotlin
class OuterClass {
    val outerValue = "Outer Value"

    class NestedClass {
        fun show() = "outerValue에 접근 불가"   // outerValue 참조 시 컴파일 오류
    }
}

// 바깥 인스턴스 없이 독립적으로 생성
val nested = OuterClass.NestedClass()
```

## inner class {#inner}

`inner` 키워드를 붙이면, 이 클래스는 **자신을 만든 바깥 클래스 인스턴스에 대한 참조를 유지**합니다. 그래서 `private` 멤버까지 포함해 바깥 클래스의 모든 멤버에 자유롭게 접근할 수 있습니다.

```kotlin
class OuterClass(val name: String) {
    private val secret = "Secret Code"

    inner class InnerClass {
        fun reveal() = "Outer name: $name, Secret: $secret"   // 바깥 멤버 접근 OK
    }
}

fun main() {
    val outer = OuterClass("OuterName")
    val inner = outer.InnerClass()   // 바깥 인스턴스가 있어야 생성 가능
    println(inner.reveal())          // Outer name: OuterName, Secret: Secret Code
}
```

바깥 인스턴스를 명시적으로 가리켜야 할 때는 `this@OuterClass` 문법을 씁니다(이름이 겹칠 때 특히 유용).

```kotlin
class OuterClass(val name: String) {
    inner class InnerClass {
        fun showOuterReference() = this@OuterClass.name
    }
}
```

## 차이 정리 {#difference}

| | nested class (기본) | inner class (`inner`) |
|---|---|---|
| 바깥 인스턴스 참조 | 없음 | 있음(숨은 참조 유지) |
| 바깥 멤버 접근 | 불가 | 가능(`private`까지) |
| 생성 방법 | `Outer.Nested()` | `outer.Inner()` (바깥 인스턴스 필요) |
| Java 대응 | `static` 중첩 클래스 | non-`static` 중첩 클래스 |
| 메모리 안전성 | 안전(누수 위험 없음) | 바깥을 붙잡아 둠(누수 주의) |

## 바이트코드로 보는 차이 {#bytecode}

구문 차이는 `inner` 한 단어지만, 컴파일된 결과는 근본적으로 다릅니다.

```kotlin
class Vehicle(val brand: String) {
    class Wheel(val rimSize: Int)          // nested
    inner class Engine(val cylinderCount: Int) {   // inner
        fun start() = "$brand, $cylinderCount기통"  // 바깥 brand 접근
    }
}
```

이를 디컴파일하면 두 갈래로 갈립니다(핵심만 발췌).

```java
public final class Vehicle {
    private final String brand;

    // nested → static 중첩 클래스: 바깥 참조 없음
    public static final class Wheel {
        private final int rimSize;
        public Wheel(int rimSize) { this.rimSize = rimSize; }
    }

    // inner → non-static 중첩 클래스: 바깥 참조를 숨은 필드로 주입
    public final class Engine {
        private final int cylinderCount;
        public final Vehicle this$0;   // ← 바깥 Vehicle 인스턴스에 대한 강한 참조

        // 생성자가 바깥 인스턴스를 첫 인자로 받는다
        public Engine(Vehicle this$0, int cylinderCount) {
            this.this$0 = this$0;
            this.cylinderCount = cylinderCount;
        }
    }
}
```

핵심은 `this$0`입니다. 컴파일러는 inner class에 `this$0`라는 **숨은 final 필드**를 넣어 바깥 인스턴스를 강하게 붙잡아 둡니다. Kotlin의 `myCar.Engine(4)` 호출이 바이트코드에서는 `new Engine(myCar, 4)`가 되는 이유죠. inner class가 바깥 멤버에 접근할 수 있는 것도, 그리고 **메모리 누수의 원인이 되는 것도** 전부 이 숨은 참조 때문입니다.

## Android에서의 메모리 누수 주의 {#memory-leak}

inner class의 편리함에는 대가가 따릅니다. inner 인스턴스가 바깥 인스턴스보다 **더 오래 살아남으면**, 그 숨은 참조가 바깥 객체의 가비지 컬렉션을 막아 누수가 됩니다. Android에서 대표적인 패턴이 있습니다.

- `Activity` 안의 `inner class`로 만든 리스너·콜백을 오래 사는 곳(싱글톤, 백그라운드 스레드, `Handler` 큐 등)에 넘기면, 그 리스너가 `Activity`를 붙잡아 화면이 닫혀도 `Activity`가 메모리에서 해제되지 않는다.

해결책은 보통 **inner를 떼고(= static nested로) + 필요한 참조는 `WeakReference`로** 넘기는 것입니다. "기본 nested(분리)가 안전, inner는 명시적 옵트인"이라는 Kotlin의 설계 의도가 그대로 이 조언으로 이어집니다.

> **정리 감각** — 바깥 상태에 접근할 필요가 없다면 그냥 nested(기본)로 두세요. inner는 "바깥 인스턴스와 생명주기를 같이 가도 안전할 때"만 의도적으로 선택하는 기능입니다. 편의를 얻는 대신 생명주기 관리 책임이 따라옵니다.

## 요약 {#summary}

> **TL;DR** — 중첩 클래스의 기본은 **nested**(바깥 참조 없음 = Java의 static 중첩). `inner`를 붙이면 바깥 인스턴스를 `this$0` 숨은 참조로 붙잡아, 바깥 멤버(`private` 포함)에 접근할 수 있습니다. 그 대가로 바깥 객체를 살려 두므로, 특히 Android에서 리스너·콜백으로 쓰면 메모리 누수를 조심해야 합니다. Java와 기본값이 정반대라는 점을 기억하세요.

1. **기본 = nested**: 바깥 참조 없음, `Outer.Nested()`로 독립 생성, 누수 위험 없음.
2. **`inner`**: 바깥 인스턴스 참조 유지, `outer.Inner()`로 생성, 바깥 멤버(`private`까지) 접근.
3. **Java와 반대**: Java는 기본 non-static, Kotlin은 기본 분리(static 상당). `inner`가 옵트인.
4. **바이트코드**: inner는 `this$0` 숨은 필드로 바깥을 강하게 참조 → 접근 능력과 누수 위험의 근원.
5. **Android 누수**: `Activity` inner 리스너가 오래 살면 `Activity` 누수. static nested + `WeakReference`로 회피.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) nested class와 inner class의 차이는 무엇인가요?">

`inner` 없이 선언한 nested class는 바깥 클래스 인스턴스에 대한 참조를 가지지 않아(Java의 static 중첩 클래스처럼) 바깥 멤버에 접근할 수 없고, `Outer.Nested()`로 독립 생성됩니다. `inner`를 붙인 inner class는 바깥 인스턴스에 대한 참조를 유지해 `private`을 포함한 바깥 멤버에 접근할 수 있으며, 생성하려면 바깥 인스턴스가 필요합니다(`outer.Inner()`).

</def>
<def title="Q) Kotlin의 기본 중첩 클래스가 Java와 다른 점은?">

Java는 중첩 클래스가 기본적으로 바깥 인스턴스를 참조하는 non-static이고, `static`을 붙여야 분리됩니다. Kotlin은 정반대로 기본이 분리(nested, static 상당)이고 `inner`를 붙여야 바깥을 참조합니다. 즉 Kotlin은 "누수 위험이 없는 안전한 쪽"을 기본값으로 두고, 바깥 참조가 필요한 경우에만 `inner`로 명시적으로 옵트인하도록 설계했습니다.

</def>
<def title="Q) inner class가 메모리 누수를 일으킬 수 있는 이유는?">

컴파일러가 inner class에 `this$0`라는 숨은 필드를 주입해 바깥 인스턴스를 **강하게 참조**하기 때문입니다. inner 인스턴스가 바깥 인스턴스보다 오래 살아남으면 이 참조가 바깥 객체의 가비지 컬렉션을 막습니다. Android에서 `Activity`의 inner class 리스너·콜백을 오래 사는 객체(싱글톤, `Handler`, 백그라운드 스레드)에 넘기면 `Activity`가 해제되지 않는 누수가 대표적입니다. static nested class로 바꾸고 필요한 참조를 `WeakReference`로 넘겨 회피합니다.

</def>
<def title="Q) 바깥 클래스 인스턴스를 명시적으로 가리키려면?">

`this@OuterClass` 문법을 사용합니다. inner class 안에서 그냥 `this`는 inner 자신을 가리키므로, 바깥 인스턴스를 참조하거나 이름이 겹치는 멤버를 구분해야 할 때 `this@OuterClass.name`처럼 씁니다.

</def>
</deflist>
