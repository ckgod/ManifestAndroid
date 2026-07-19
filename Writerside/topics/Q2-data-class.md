# Q2) data class와 일반 class의 차이

서버에서 받은 JSON, DB에서 읽은 한 행(row), 화면에 뿌릴 UI 상태 — 우리가 다루는 데이터의 상당수는 **"값을 담기만 하는 객체"** 입니다. 이런 객체는 로직보다 데이터 그 자체가 중요하고, 그래서 늘 똑같은 뒤처리가 따라붙습니다. "두 객체의 내용이 같은지 비교하고, 로그로 예쁘게 찍고, 일부만 바꿔 복제하고…".

`data class`는 바로 이 반복 작업을 없애기 위한 **데이터 전용 클래스**입니다. 개발자가 손으로 써야 했던 표준 메서드들을 **컴파일러가 대신 생성**해 주죠. 한 문장으로 요약하면 이렇습니다.

> **일반 `class`는 "동작을 담는 객체", `data class`는 "값을 담는 객체".**
> 그리고 값을 담는 객체에 꼭 필요한 잡일(비교·출력·복사·분해)을 컴파일러가 대신 처리해 줍니다.

## 먼저 그림부터: 무엇이 달라지나 {#big-picture}

같은 프로퍼티를 가진 두 클래스를 나란히 두면 차이가 한눈에 들어옵니다.

| 해 보는 것 | 일반 `class` | `data class` |
|---|---|---|
| 내용이 같은 두 객체 `==` 비교 | `false` (주소 비교) | `true` (값 비교) |
| `println(user)` | `User@1f32e575` | `User(name=Alice, age=30)` |
| 구조 분해 `val (a, b) = user` | 불가 (컴파일 오류) | 가능 |
| 일부만 바꿔 복제 `user.copy(...)` | 불가 (컴파일 오류) | 가능 |

일반 클래스에서 이 넷을 다 쓰려면 `equals()`·`hashCode()`·`toString()`·`copy()`·`componentN()`을 직접 써야 합니다. `data`를 한 단어 붙이면 컴파일러가 이걸 전부 만들어 줍니다.

## data class가 되기 위한 조건 {#requirements}

아무 클래스에나 `data`를 붙일 수 있는 건 아닙니다. 컴파일러가 "프로퍼티를 기준으로" 메서드를 만들어 줘야 하므로, 그 전제가 되는 규칙이 있습니다.

- 주 생성자에 **매개변수가 최소 하나**는 있어야 한다. (담을 데이터가 있어야 하니까)
- 주 생성자의 모든 매개변수는 **`val` 또는 `var`** 로 선언돼야 한다. (프로퍼티여야 비교·복사의 대상이 됨)
- `abstract`·`open`·`sealed`·`inner`가 될 수 **없다**.

> **왜 이런 제약이 있을까** — `data class`의 자동 생성 메서드는 전부 "주 생성자에 선언된 프로퍼티"를 재료로 삼습니다. 그래서 재료(프로퍼티)가 반드시 있어야 하고, 상속처럼 프로퍼티 구성이 흔들릴 수 있는 형태(`open`·`abstract`)는 막아 둔 것입니다.

## 컴파일러가 대신 써 주는 5가지 {#generated-functions}

`data`를 붙이는 순간 컴파일러가 만들어 주는 함수는 다섯입니다. 각각 "왜 필요한지"와 함께 보겠습니다.

1. **`equals()` — 내용으로 같은지 비교한다.**
   두 인스턴스의 주 생성자 프로퍼티 값이 모두 같으면 `true`. 즉 "같은 객체냐(주소)"가 아니라 **"내용이 같냐"** 를 따지는 **구조적 동등성**입니다. 데이터를 비교할 때 우리가 진짜 원하는 동작이죠.
2. **`hashCode()` — `equals()`와 짝을 이룬다.**
   프로퍼티들의 해시를 조합해 계산합니다. "내용이 같으면 해시도 같다"를 보장하기 때문에, `HashSet`·`HashMap`의 **키로 안전하게** 쓸 수 있습니다. (이 약속이 깨지면 Set에 중복이 들어가는 등 컬렉션이 오작동합니다.)
3. **`toString()` — 사람이 읽을 수 있게 출력한다.**
   `User(name=Alice, age=30)`처럼 클래스명과 프로퍼티 이름-값을 나열합니다. 로깅·디버깅에서 객체 상태를 바로 확인할 수 있습니다.
4. **`copy()` — 일부만 바꿔 새 인스턴스를 만든다.**
   기존 객체는 그대로 두고, 지정한 프로퍼티만 바꾼 **새 객체**를 반환합니다. 불변(immutable) 데이터를 다룰 때 "이전 상태에서 다음 상태를 파생"시키기에 편합니다. (예: `state.copy(isLoading = false)`)
5. **`componentN()` — 구조 분해를 가능하게 한다.**
   프로퍼티마다 선언 순서대로 `component1()`, `component2()`… 를 만듭니다. 이 덕분에 `val (name, age) = user`처럼 한 번에 풀어 쓸 수 있습니다.

> **`copy()`와 불변성 논쟁** — `copy()`는 불변 객체 갱신을 편하게 해 주지만, 결국 값을 바꿔 새 인스턴스를 찍어내는 통로이기도 합니다. 그래서 "진짜 불변이라면 `copy()`조차 없어야 하는 것 아니냐"는 견해도 있습니다. 편의와 불변의 순수성 사이의 트레이드오프로 이해하면 됩니다.

## 일반 class와 나란히 비교 {#comparison}

앞의 표를 실제 코드로 확인해 봅시다.

```kotlin
class NormalUser(val name: String, val age: Int)

data class DataUser(val name: String, val age: Int)

fun main() {
    val normalUser1 = NormalUser("Alice", 30)
    val normalUser2 = NormalUser("Alice", 30)

    val dataUser1 = DataUser("Alice", 30)
    val dataUser2 = DataUser("Alice", 30)

    // 1. equals() — 일반 클래스는 주소 비교, data class는 내용 비교
    println(normalUser1 == normalUser2) // false (내용은 같지만 다른 객체)
    println(dataUser1 == dataUser2)     // true  (프로퍼티 값이 같음)

    // 2. toString()
    println(normalUser1) // NormalUser@1f32e575  (정체를 알 수 없는 출력)
    println(dataUser1)   // DataUser(name=Alice, age=30)

    // 3. componentN()을 이용한 구조 분해
    val (name, age) = dataUser1
    println("Name: $name, Age: $age") // Name: Alice, Age: 30
    // val (n, a) = normalUser1       // 컴파일 오류 — componentN()이 없음

    // 4. copy()
    val dataUser3 = dataUser1.copy(age = 31)
    println(dataUser3) // DataUser(name=Alice, age=31)
    // normalUser1.copy()             // 컴파일 오류 — copy()가 없음
}
```

자동 생성 함수 말고도, 정리해 두면 좋은 개념적 차이가 세 가지 있습니다.

1. **보일러플레이트**: 일반 클래스는 `equals()`·`hashCode()`·`toString()`을 직접 재정의해야 하지만, data class는 컴파일러가 만들어 준다.
2. **주 생성자 요구**: data class는 주 생성자에 프로퍼티가 최소 하나 필요하지만, 일반 클래스는 그렇지 않다.
3. **용도**: data class는 DB·네트워크 같은 I/O로 오가는 **읽기 전용 도메인 데이터**를 담는 데, 일반 클래스는 동작·로직을 담는 모든 객체에 쓴다.

## 바이트코드로 보는 data class의 정체 {#bytecode}

Java에서 넘어왔다면 `data`가 마법처럼 느껴질 수 있습니다. 하지만 디컴파일해 보면 마법이 아니라, **컴파일러가 우리 대신 코드를 잔뜩 써 준 것뿐**임이 드러납니다.

```kotlin
data class User(val name: String, val age: Int)
```

이 한 줄을 디컴파일하면 대략 아래 Java 클래스가 됩니다(핵심만 발췌).

```java
// data class는 상속 불가능한 final 클래스가 된다
public final class User {
    private final String name;
    private final int age;

    // 1. 생성자 + 각 프로퍼티의 getter
    public User(String name, int age) { this.name = name; this.age = age; }
    public final String getName() { return this.name; }
    public final int getAge() { return this.age; }

    // 2. 구조 분해를 위한 componentN()
    public final String component1() { return this.name; }
    public final int component2() { return this.age; }

    // 3. copy() — 내부적으로 new User(...)를 호출한다
    public final User copy(String name, int age) { return new User(name, age); }

    // 4. 읽기 좋은 toString()
    public String toString() { return "User(name=" + this.name + ", age=" + this.age + ")"; }

    // 5. 내용 기반 hashCode()
    public int hashCode() { return this.name.hashCode() * 31 + this.age; }

    // 6. 구조적 equals()
    public boolean equals(Object other) {
        if (this == other) return true;
        if (!(other instanceof User)) return false;
        User o = (User) other;
        return this.name.equals(o.name) && this.age == o.age;
    }
}
```

즉 `data` 키워드는 컴파일러에게 **"이 여섯 부류의 코드를 대신 생성하라"** 는 지시입니다. 이 메서드들은 컴파일 시점에 바이트코드로 만들어지며, 그게 전부입니다. 처음엔 마법 같아 보여도, 결국 컴파일러가 보이지 않는 곳에서 손품을 대신 팔아 주는 것뿐입니다.

## Pro Tips {#pro-tips}

> **`copy()`의 가시성 변경 (Kotlin 2.0.20~)** — 지금까지는 `private` 생성자로 data class를 만들어도 자동 생성된 `copy()`는 그 `private`을 물려받지 않아, 외부에서 `copy()`로 인스턴스를 만들어 내는 허점이 있었습니다. 아래처럼 팩토리로만 생성을 통제하려 해도 `copy()`가 뒷문이 됩니다.
>
> ```kotlin
> data class PositiveInteger private constructor(val number: Int) {
>     companion object {
>         fun create(number: Int): PositiveInteger? =
>             if (number > 0) PositiveInteger(number) else null
>     }
> }
>
> val positive = PositiveInteger.create(42) ?: return
> val broken = positive.copy(number = -1) // 뒷문: 음수 인스턴스가 만들어짐
> ```
>
> 향후 Kotlin에서는 `copy()`의 기본 가시성이 **생성자의 가시성과 일치**하도록 바뀝니다. Kotlin 2.0.20부터 영향받는 코드에 경고를 띄우며, 점진적 마이그레이션을 위해 `@ConsistentCopyVisibility`(새 동작 미리 적용)와 `@ExposedCopyVisibility`(기존 동작 유지·경고 무시) 어노테이션, 그리고 모듈 전체에 적용하는 `-Xconsistent-data-class-copy-visibility` 컴파일러 옵션을 제공합니다.

> **data class는 상속할 수 없다 (그리고 그 논의)** — `data class`는 `final`이라 다른 클래스가 상속할 수 없고, data class 자신도 `open`일 수 없습니다. `equals()`/`hashCode()` 같은 자동 생성 메서드가 상속 계층에서 일관성을 지키기 어렵기 때문입니다. 이 제약을 풀려는 [KEEP 제안(data class inheritance)](https://github.com/Kotlin/KEEP/blob/master/proposals/data-class-inheritance.md)이 논의 중이지만, `componentN()` 재정의·생성자 매개변수 관리 등 풀어야 할 문제가 남아 있습니다.

## 요약 {#summary}

> **TL;DR** — `data class`는 값을 담는 데 특화된 클래스로, 컴파일러가 `equals()`·`hashCode()`·`toString()`·`copy()`·`componentN()`을 자동 생성합니다. 그래서 `==`는 주소가 아닌 **내용**을 비교하고, 구조 분해와 불변 갱신(`copy()`)이 가능해집니다. 일반 클래스는 이런 메서드를 기본 제공하지 않는 대신 동작·로직을 담는 데 더 유연합니다.

1. **자동 생성 5종**: `equals()`(구조적 동등성)·`hashCode()`·`toString()`·`copy()`·`componentN()`을 컴파일러가 만들어 준다.
2. **조건**: 주 생성자에 `val`/`var` 프로퍼티가 최소 하나 있어야 하고, `abstract`·`open`·`sealed`·`inner`일 수 없다.
3. **핵심 차이**: 일반 클래스의 `==`는 주소 비교라 값이 같아도 `false`지만, data class는 내용 비교라 `true`다. 구조 분해와 `copy()`도 data class에만 있다.
4. **용도**: data class는 I/O로 오가는 읽기 전용 도메인 데이터에, 일반 클래스는 동작·로직을 담는 객체에 적합하다.
5. **정체**: `data`는 마법이 아니라, 컴파일 시점에 관련 메서드를 바이트코드로 생성하라는 컴파일러 지시일 뿐이다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) data class를 선언하면 컴파일러가 무엇을 생성하나요?">

주 생성자 프로퍼티를 기반으로 다섯 가지를 자동 생성합니다. 구조적 동등성을 비교하는 `equals()`, 그와 일관된 `hashCode()`, 읽기 좋은 `toString()`, 일부 프로퍼티만 바꿔 새 인스턴스를 만드는 `copy()`, 그리고 구조 분해를 지원하는 `component1()`·`component2()`… 입니다. 덕분에 일반 클래스라면 손으로 써야 할 보일러플레이트가 사라집니다.

</def>
<def title="Q) 일반 class와 data class의 == 동작은 어떻게 다른가요?">

일반 클래스는 `equals()`를 재정의하지 않으면 `Any`의 기본 구현, 즉 **참조(주소) 동등성**을 씁니다. 그래서 프로퍼티 값이 같아도 서로 다른 객체면 `==`가 `false`입니다. 반면 data class는 컴파일러가 **구조적 동등성** `equals()`를 생성하므로, 주 생성자 프로퍼티 값이 모두 같으면 `==`가 `true`가 됩니다.

</def>
<def title="Q) data class가 되기 위한 조건은 무엇인가요?">

주 생성자에 매개변수가 최소 하나 있어야 하고, 그 매개변수들은 모두 `val` 또는 `var`로 선언돼야 합니다. 또한 `abstract`·`open`·`sealed`·`inner` 클래스는 data class가 될 수 없습니다. 이 제약들은 컴파일러가 프로퍼티를 재료로 삼아 `equals()` 등을 안전하게 생성하기 위한 전제입니다.

</def>
<def title="Q) copy()가 불변성 관점에서 논쟁이 되는 이유는 무엇인가요?">

`copy()`는 불변 객체를 다룰 때 기존 상태에서 일부만 바꾼 새 인스턴스를 쉽게 파생시켜 주는 편리한 함수입니다. 다만 "완전한 불변이라면 값을 바꿀 통로 자체가 없어야 한다"는 관점에서 보면, 프로퍼티 값을 바꿔 새 인스턴스를 만드는 `copy()`가 불변의 순수성을 다소 퇴색시킨다고 볼 수도 있습니다. 편의와 순수성 사이의 트레이드오프입니다.

</def>
<def title="Q) private 생성자로 data class를 만들면 copy()에 어떤 허점이 있나요?">

지금까지는 생성자를 `private`으로 막아도 자동 생성된 `copy()`는 그 가시성을 물려받지 않았습니다. 그래서 팩토리 함수로 생성을 통제하려 해도, 외부에서 `copy()`를 호출해 검증을 우회한 인스턴스를 만들 수 있는 뒷문이 생겼습니다. Kotlin 2.0.20부터는 이런 코드에 경고를 띄우며, 향후 `copy()`의 기본 가시성이 생성자와 일치하도록 바뀝니다. 마이그레이션을 위해 `@ConsistentCopyVisibility`·`@ExposedCopyVisibility` 어노테이션을 제공합니다.

</def>
</deflist>
</content>
</invoke>
