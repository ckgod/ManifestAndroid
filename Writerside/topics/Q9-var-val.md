# Q9) var와 val의 차이점은 무엇인가

`var`는 **가변**, `val`은 **읽기 전용**입니다. 둘의 차이는 "값을 바꿀 수 있느냐"가 아니라 **"참조를 다시 할당할 수 있느냐"** 입니다. 이 한 글자 차이로 변수의 의도가 코드에 드러납니다.

```kotlin
var counter = 0
counter += 1          // OK — 재할당 가능

val name = "Kotlin"
// name = "Java"      // 컴파일 오류 — 재할당 불가
```

가장 흔한 오해가 여기서 시작됩니다. `val`은 불변(immutable)이 아닙니다.

## 기본 차이 {#basics}

| | `var` | `val` |
|---|---|---|
| 재할당 | 가능 | 불가 |
| 생성되는 접근자 | getter + setter | getter만 |
| 초기화 시점 | 선언 시 또는 이후 | 선언 시 또는 `init`/생성자에서 한 번 |
| 오버라이드 | `var`로만 | `val` 또는 `var` 둘 다 |
| Java 대응 | 일반 필드 | 상황에 따라 다름(아래 참고) |

기본 지침은 단순합니다. **일단 `val`로 쓰고, 재할당이 필요할 때만 `var`로 바꿉니다.** 재할당되지 않는다는 사실이 보장되면 코드를 읽을 때 추적해야 할 상태가 그만큼 줄어듭니다.

## val은 참조를 고정할 뿐이다 {#reference-not-object}

`val`이 보장하는 것은 **참조가 다른 객체를 가리키지 않는다**는 것뿐입니다. 그 객체 내부가 바뀌는 것은 막지 못합니다.

```kotlin
val numbers = mutableListOf(1, 2, 3)
numbers.add(4)              // OK — 리스트 내용은 바뀐다
println(numbers)            // [1, 2, 3, 4]

// numbers = mutableListOf() // 컴파일 오류 — 참조 재할당만 막힌다
```

그래서 `val`을 "읽기 전용"이라고 부르기보다 **참조 불변성(참조는 못 바꿈) + 객체 가변성(객체는 바꿀 수 있음)** 으로 설명하는 편이 정확합니다.

타입을 읽기 전용 인터페이스로 선언해도 완전한 방어는 되지 않습니다.

```kotlin
val list: List<Int> = mutableListOf(1, 2, 3)
// list.add(4)                      // List에는 add가 없다 — 여기까지는 막힌다
(list as MutableList<Int>).add(4)   // 하지만 캐스팅하면 뚫린다
```

`List`는 **불변 타입이 아니라 읽기 전용 인터페이스**입니다. 실제 객체가 `MutableList`라면 캐스팅으로 우회할 수 있습니다. 외부에 넘길 때 방어가 필요하면 `toList()`로 복사본을 주는 편이 안전합니다.

## val이 매번 같은 값을 준다는 보장도 없다 {#custom-getter}

한 걸음 더 나갑니다. `val`에 커스텀 getter를 달면 **접근할 때마다 다른 값이 나옵니다.**

```kotlin
import kotlin.random.Random

val random: Int
    get() = Random.nextInt()

println(random)   // 예: 482913
println(random)   // 예: -71204  — 같은 val인데 값이 다르다
```

`val`이 금지하는 것은 **재할당(`=` 연산)** 이지 값의 고정이 아닙니다. 커스텀 getter를 쓰면 저장 공간 없이 매번 계산된 결과가 반환됩니다.

Android에서 자주 보는 형태입니다.

```kotlin
val isLoggedIn: Boolean
    get() = token != null     // token이 바뀌면 결과도 바뀐다
```

## val과 const val {#const}

`val`은 **런타임에** 평가됩니다. 값이 함수 호출 결과여도 됩니다.

```kotlin
val timestamp = System.currentTimeMillis()   // OK — 실행 시점에 결정
```

반면 `const val`은 **컴파일 타임 상수**입니다. 제약이 따릅니다.

- 최상위 또는 `object`(`companion object` 포함) 안에서만 선언 가능
- primitive 타입과 `String`만 가능
- 커스텀 getter 불가

```kotlin
object Config {
    const val MAX_COUNT = 100
    // const val NOW = System.currentTimeMillis()  // 오류 — 컴파일 타임에 정해지지 않음
}
```

차이가 실제로 드러나는 곳은 바이트코드입니다. `const val`은 호출부에 **값 자체가 박힙니다.**

```java
// println(Config.MAX_COUNT) 를 컴파일한 결과
0: bipush        100        // 필드를 읽지 않고 100이 그대로 들어감
2: istore_0
```

여기서 실무적인 함의가 하나 나옵니다. 라이브러리가 공개한 `const val`을 사용하는 앱은 **그 값을 자기 바이트코드에 복사해 갑니다.** 라이브러리에서 상수 값을 바꾸고 라이브러리만 교체하면, 앱은 옛날 값을 그대로 씁니다. 재컴파일해야 반영됩니다. 모듈 경계를 넘는 상수라면 이 점을 염두에 둬야 합니다.

## Pro Tips {#pro-tips}

### 바이트코드로 보는 val과 var {#bytecode}

프로퍼티가 실제로 어떻게 컴파일되는지 보면 차이가 분명해집니다.

```kotlin
class E {
    val readOnly: Int = 1
    var mutable: Int = 2
}
```

`javap -p`로 확인한 결과입니다.

```java
public final class E {
  private final int readOnly;      // final 필드
  private int mutable;             // 일반 필드
  public final int getReadOnly();  // getter만
  public final int getMutable();
  public final void setMutable(int);   // var에만 setter
}
```

정리하면 이렇습니다.

- `val` → `private final` 필드 + getter
- `var` → `private` 필드 + getter + setter

Kotlin에서 프로퍼티에 직접 접근하는 것처럼 보이는 `obj.readOnly`는 실제로는 `obj.getReadOnly()` 호출입니다. 같은 클래스 안에서는 컴파일러가 필드 직접 접근으로 최적화합니다.

### val을 var로 오버라이드할 수 있다 {#override}

`val`은 "getter만 있는 프로퍼티"이므로, 하위 클래스에서 setter를 추가하는 것은 계약 위반이 아닙니다.

```kotlin
open class A { open val x: Int = 1 }
class B : A() { override var x: Int = 2 }   // val → var 오버라이드, 컴파일 통과
```

반대 방향은 막힙니다. 상위가 `var`인데 하위에서 `val`로 좁히면 setter가 사라져 계약이 깨지기 때문입니다.

```kotlin
open class A2 { open var x: Int = 1 }
class B2 : A2() { override val x: Int = 2 }
```

```
error: 'var' property 'var x: Int' defined in 'A2' cannot be overridden by 'val' property 'val x: Int'.
```

이 사실은 `val`이 곧 `final`이 아니라는 근거이기도 합니다. **인터페이스에 `val`을 선언했다고 해서 구현체가 그 값을 고정한다는 보장은 없습니다.**

### Java의 final과 같은가 {#vs-final}

같지 않습니다. 위치에 따라 다릅니다.

| | Kotlin | Java 대응 |
|---|---|---|
| 지역 변수 `val` | 재할당 불가 | `final` 지역 변수와 사실상 동일 |
| 프로퍼티 `val` (backing field 있음) | getter만 노출 | `private final` 필드 + getter |
| 프로퍼티 `val` (커스텀 getter) | 저장 공간 없음 | getter 메서드만 |
| `const val` | 컴파일 타임 상수 | `public static final` + 호출부 인라인 |

지역 변수 `val`만 Java의 `final`과 거의 같고, 프로퍼티 `val`은 "값이 고정된 필드"가 아니라 **"setter가 없는 프로퍼티"** 입니다.

### 진짜 불변을 원한다면 {#immutability}

`val`만으로는 부족합니다. 단계별로 정리하면 이렇습니다.

1. **`val` + 불변 타입 조합** — 프로퍼티를 `val`로 선언하고, 타입도 `String`·`Int`처럼 불변인 것으로 둡니다.
2. **`data class` + 전부 `val`** — 상태 변경은 `copy()`로 새 객체를 만들어 대체합니다. Compose의 State나 MVI의 UiState가 이 방식입니다.
3. **불변 컬렉션 라이브러리** — 캐스팅 우회까지 막으려면 [kotlinx.collections.immutable](https://github.com/Kotlin/kotlinx.collections.immutable)의 `PersistentList` 같은 타입을 씁니다. Compose에서는 안정성(Stability) 판정에도 유리합니다.

> **Compose 맥락** — `val`이 붙었다고 Compose가 안정(stable)하다고 판단하지는 않습니다. 프로퍼티가 전부 `val`이고 타입까지 안정적이어야 합니다. `val list: List<Item>`은 `List`가 읽기 전용 인터페이스일 뿐 불변 보장이 없어 불안정으로 취급됩니다.

## 요약 {#summary}

> **TL;DR** — `var`는 재할당 가능, `val`은 재할당 불가입니다. `val`이 보장하는 것은 **참조 불변성**뿐이며 객체 내부는 얼마든지 바뀔 수 있습니다. 커스텀 getter를 달면 접근할 때마다 값이 달라질 수도 있습니다. 바이트코드에서 `val`은 `private final` 필드 + getter, `var`는 setter까지 생성됩니다. 컴파일 타임 상수가 필요하면 `const val`을 쓰되, 호출부에 값이 인라인되므로 모듈 경계에서는 주의가 필요합니다.

1. **핵심 차이**: `var`는 재할당 가능, `val`은 불가. `val`은 getter만, `var`는 getter + setter가 생성됨.
2. **val ≠ 불변**: 참조만 고정할 뿐 객체 내부는 변경 가능(`val list = mutableListOf()`에 `add` 가능).
3. **val ≠ 값 고정**: 커스텀 getter를 쓰면 접근할 때마다 다른 값이 나올 수 있음.
4. **읽기 전용 타입도 완전하지 않음**: `List`는 불변 타입이 아니라 읽기 전용 인터페이스. 캐스팅으로 우회 가능.
5. **const val**: 컴파일 타임 상수로 호출부에 인라인됨. 라이브러리 상수 변경 시 사용처 재컴파일 필요.
6. **오버라이드**: `val` → `var`는 가능, `var` → `val`은 불가. `val`은 `final`이 아님.
7. **기본 전략**: 일단 `val`, 재할당이 꼭 필요할 때만 `var`.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) var와 val의 차이점은 무엇인가요?">

`var`는 가변 변수로 초기화 이후에도 값을 재할당할 수 있고, `val`은 읽기 전용이라 초기화 이후 재할당할 수 없습니다. 컴파일 결과에서도 차이가 나는데, `val`은 `private final` 필드와 getter만 생성되고 `var`는 여기에 setter가 추가됩니다. 다만 `val`이 보장하는 것은 참조가 다른 객체를 가리키지 않는다는 것뿐이며 불변성을 의미하지는 않습니다. 기본적으로 `val`을 사용하고 재할당이 반드시 필요한 경우에만 `var`를 쓰는 것이 권장됩니다.

</def>
<def title="Q) val로 선언하면 값이 바뀌지 않는다고 볼 수 있나요?">

아닙니다. `val`은 참조 재할당만 막을 뿐 객체 내부 상태 변경은 막지 못합니다. `val numbers = mutableListOf(1, 2, 3)`에서 `numbers.add(4)`는 정상 동작하며, 막히는 것은 `numbers = 다른리스트` 같은 재할당뿐입니다. 또한 커스텀 getter를 정의하면 접근할 때마다 다른 값이 반환될 수도 있습니다. 정확히는 참조 불변성은 보장하되 객체 가변성은 그대로 남는다고 설명하는 것이 맞습니다. 진짜 불변성이 필요하면 불변 타입을 쓰거나 `kotlinx.collections.immutable` 같은 라이브러리를 사용해야 합니다.

</def>
<def title="Q) val과 const val의 차이는 무엇인가요?">

`val`은 런타임에 평가되므로 `System.currentTimeMillis()` 같은 함수 호출 결과도 담을 수 있지만, `const val`은 컴파일 타임에 값이 결정되어야 합니다. 그래서 `const val`은 최상위나 `object`(`companion object` 포함) 안에서만 선언할 수 있고 primitive 타입과 `String`만 허용되며 커스텀 getter를 쓸 수 없습니다. 바이트코드에서도 차이가 나는데, `const val`은 호출부에 값 자체가 인라인됩니다. 따라서 라이브러리가 공개한 `const val` 값을 변경하면 그것을 사용하는 코드를 재컴파일해야 반영됩니다.

</def>
<def title="Q) val 프로퍼티는 Java의 final 필드와 같나요?">

같지 않습니다. 지역 변수로 쓰인 `val`은 Java의 `final` 지역 변수와 사실상 동일하지만, 클래스 프로퍼티로 쓰인 `val`은 "값이 고정된 필드"가 아니라 "setter가 없는 프로퍼티"입니다. backing field가 있으면 `private final` 필드와 getter로 컴파일되지만, 커스텀 getter를 쓰면 필드 없이 getter 메서드만 생성됩니다. 결정적으로 `val` 프로퍼티는 하위 클래스에서 `var`로 오버라이드할 수 있어 setter가 추가될 수 있습니다. 즉 인터페이스에 `val`로 선언했다고 해서 구현체가 값을 고정한다는 보장은 없습니다.

</def>
<def title="Q) val을 var로 오버라이드할 수 있나요?">

가능합니다. `val`은 getter만 요구하는 계약이므로, 하위 클래스가 setter를 추가로 제공하는 것은 계약을 넓히는 것이라 허용됩니다. 반대로 상위가 `var`인데 하위에서 `val`로 오버라이드하는 것은 setter가 사라져 계약이 깨지므로 컴파일 오류가 발생합니다. 이는 `val`이 `final`과 다르다는 점을 보여주는 사례이기도 합니다.

</def>
<def title="Q) 읽기 전용 타입인 List를 쓰면 불변이 보장되나요?">

보장되지 않습니다. Kotlin의 `List`는 불변 타입이 아니라 읽기 전용 인터페이스이며, 실제 인스턴스가 `MutableList`라면 `(list as MutableList<Int>).add(4)`처럼 캐스팅으로 변경할 수 있습니다. 외부에 컬렉션을 노출할 때 방어가 필요하면 `toList()`로 복사본을 전달하거나, `kotlinx.collections.immutable`의 `PersistentList` 같은 실제 불변 타입을 사용해야 합니다. Compose에서 `List` 타입 프로퍼티가 불안정(unstable)으로 판정되는 이유도 같은 맥락입니다.

</def>
</deflist>
