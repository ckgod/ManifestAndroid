# Q2) data class와 일반 class의 차이

`data class`는 이름 그대로 **데이터를 담기 위해** 특별히 설계된 클래스입니다. 데이터 컨테이너 역할을 하는 클래스를 간결하게 만들 수 있게 해 주며, 일반 `class`라면 손으로 작성해야 할 표준적인 메서드들을 **컴파일러가 대신 생성**해 줍니다.

서버에서 받은 JSON, DB에서 읽은 한 행(row), 화면에 뿌릴 UI 상태처럼 우리가 다루는 객체의 상당수는 "값을 담는 것"이 주 목적입니다. 이런 객체에는 늘 똑같은 뒤처리 — 내용이 같은지 비교하고, 로그로 찍고, 일부만 바꿔 복제하는 — 가 따라붙는데, `data class`는 그 반복을 컴파일러에게 떠넘기는 장치입니다.

## data class의 조건 {#requirements}

아무 클래스에나 `data`를 붙일 수 있는 것은 아닙니다. 다음 요구 사항을 만족해야 합니다.

- 주 생성자에 **최소 하나의 매개변수**가 있어야 한다.
- 모든 주 생성자 매개변수는 `val` 또는 `var`로 선언돼야 한다.
- `abstract`, `open`, `sealed`, `inner`가 될 수 없다.

이 제약들은 자의적인 규칙이 아닙니다. `data class`의 자동 생성 메서드는 전부 **주 생성자에 선언된 프로퍼티**를 재료로 삼습니다. 그래서 재료가 될 프로퍼티가 최소 하나는 있어야 하고(`val`/`var`), 상속을 통해 프로퍼티 구성이 흔들릴 수 있는 형태(`open`·`abstract`)는 애초에 허용하지 않는 것입니다.

## 컴파일러가 생성해 주는 것 {#generated-functions}

`data class`를 선언하면 컴파일러가 다음 함수들을 자동으로 만들어 줍니다.

1. **`equals()`** — 주 생성자에 선언된 모든 프로퍼티 값이 같으면 `true`를 반환하는 **구조적 동등성** 검사. 두 데이터 객체가 "내용이 같은지"를 비교할 수 있게 한다.
2. **`hashCode()`** — 주 생성자 프로퍼티들의 해시 코드를 기반으로 계산된다. 구조적으로 같은 두 인스턴스가 같은 해시 코드를 갖도록 보장하며, `HashSet`·`HashMap`의 키로 객체를 올바르게 쓰기 위한 핵심 약속이다.
3. **`toString()`** — `User(name=Alice, age=30)`처럼 클래스 이름과 프로퍼티 이름-값 쌍을 나열하는 읽기 좋은 문자열을 만든다. 로깅·디버깅에 유용하다.
4. **`copy()`** — 기존 인스턴스를 복사하되 일부 프로퍼티만 바꾼 새 인스턴스를 만든다. 불변 객체를 다룰 때 기존 상태에서 새 상태를 파생시키기 편하다.
5. **`componentN()`** — 주 생성자 프로퍼티마다 선언 순서대로 `component1()`, `component2()`… 를 만든다. 구조 분해 선언(`val (name, age) = user`)을 가능하게 하는 함수들이다.

> **`equals()`와 `hashCode()`는 왜 항상 같이 갈까** — "내용이 같으면 해시 코드도 같다"는 규약이 깨지면 해시 기반 컬렉션이 오작동합니다. 예를 들어 `HashSet`은 먼저 `hashCode()`로 저장 위치(버킷)를 찾고, 그 안에서 `equals()`로 최종 일치를 확인합니다. `equals()`만 재정의하고 `hashCode()`를 방치하면, 내용이 같은 두 객체가 서로 다른 버킷으로 흩어져 "분명 같은데 Set에 중복으로 들어가는" 버그가 생깁니다. `data class`는 이 둘을 **항상 짝으로** 생성하므로 이 문제를 원천 차단합니다.

한 가지 자주 놓치는 점은, 이 다섯 함수가 오직 **주 생성자에 선언된 프로퍼티만** 대상으로 한다는 것입니다. 클래스 본문(body)에서 선언한 프로퍼티는 `equals()`·`hashCode()`·`toString()`·`copy()` 어디에도 포함되지 않습니다.

```kotlin
data class User(val name: String) {
    var age: Int = 0   // 본문 프로퍼티 — 자동 생성 함수가 무시한다
}

val a = User("Alice").apply { age = 30 }
val b = User("Alice").apply { age = 99 }

println(a == b)   // true  — age는 비교 대상이 아니라서 name만 같으면 동등
println(a)        // User(name=Alice)  — toString에도 age가 안 나온다
```

이 동작은 버그의 원천이 될 수 있으므로, 동등성에 참여해야 하는 값이라면 반드시 **주 생성자에** 두어야 합니다.

> **`copy()`와 불변성 논쟁** — `copy()`는 불변 객체 갱신을 편하게 해 주지만, 결국 프로퍼티 값을 바꿔 새 인스턴스를 만드는 통로이기도 합니다. 이 때문에 "진정한 불변이라면 `copy()`조차 없어야 하는 것 아니냐"는 견해도 있습니다. 편의와 불변의 순수성 사이의 트레이드오프로 이해하면 됩니다.

또한 `copy()`가 만드는 것은 **얕은 복사(shallow copy)** 라는 점도 기억해 둘 필요가 있습니다. 복사되는 것은 각 프로퍼티의 참조일 뿐, 프로퍼티가 가리키는 객체 자체가 깊이 복제되지는 않습니다. 그래서 `data class`가 가변 컬렉션(`MutableList` 등)을 품고 있으면, 원본과 복사본이 **같은 리스트를 공유**해 한쪽의 변경이 다른 쪽에 새는 함정이 생깁니다. 이것이 `data class`의 프로퍼티를 되도록 불변 타입(`List`, `String` 등)으로 두라고 권하는 이유입니다.

## 일반 class와 직접 비교 {#comparison}

같은 프로퍼티를 가진 일반 클래스와 data class를 나란히 두면 차이가 분명해집니다.

```kotlin
class NormalUser(val name: String, val age: Int)

data class DataUser(val name: String, val age: Int)

fun main() {
    val normalUser1 = NormalUser("Alice", 30)
    val normalUser2 = NormalUser("Alice", 30)

    val dataUser1 = DataUser("Alice", 30)
    val dataUser2 = DataUser("Alice", 30)

    // 1. equals() — 일반 클래스는 참조 비교, data class는 내용 비교
    println(normalUser1 == normalUser2) // false (메모리상 다른 객체)
    println(dataUser1 == dataUser2)     // true  (프로퍼티 값이 같음)

    // 2. toString()
    println(normalUser1) // NormalUser@1f32e575
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

자동 생성 함수 외에 정리해 두면 좋은 차이는 다음과 같습니다.

1. **보일러플레이트**: 일반 클래스는 `equals()`·`hashCode()`·`toString()`을 직접 재정의해야 하지만, data class는 컴파일러가 만들어 준다.
2. **주 생성자 요구**: data class는 주 생성자에 최소 하나의 프로퍼티가 필요하지만, 일반 클래스는 그렇지 않다.
3. **용도**: data class는 주로 DB·네트워크 같은 I/O에서 오가는 **읽기 전용 도메인 데이터**를 담는 데 쓰이고, 일반 클래스는 동작·로직을 담는 모든 종류의 객체에 쓰인다.

> **구조 분해는 이름이 아니라 순서를 따른다** — `val (name, age) = user`는 프로퍼티 "이름"으로 매칭하는 것처럼 보이지만, 실제로는 `component1()`·`component2()`… 즉 **선언 순서**로 값을 꺼냅니다. 그래서 왼쪽 변수명은 아무 이름이나 써도 되고(`val (x, y) = user`도 동작), 반대로 주 생성자의 **프로퍼티 순서를 바꾸면** 구조 분해하던 코드가 조용히 엉뚱한 값을 집게 됩니다. data class의 프로퍼티 순서를 재배치할 때 특히 주의해야 하는 이유입니다.

## 바이트코드로 보는 data class의 정체 {#bytecode}

Java에서 넘어온 개발자라면 `data`가 마법처럼 느껴질 수 있지만, 디컴파일된 바이트코드를 보면 그 정체가 드러납니다. 사실 컴파일러가 우리 대신 코드를 잔뜩 써 줬을 뿐입니다.

```kotlin
data class User(val name: String, val age: Int)
```

이 한 줄을 디컴파일하면 대략 다음과 같은 Java 클래스가 됩니다(핵심만 발췌).

```java
// data class는 final 클래스가 된다 (상속 불가)
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

    // 3. copy() + 기본 인자 처리를 위한 synthetic copy$default()
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

즉 `data` 키워드는 컴파일러에게 "이 여섯 부류의 코드를 생성하라"는 명령입니다. 이 함수들은 **컴파일 시점에 Java 바이트코드로 생성**되며, 이것이 data class가 편의 기능을 제공하는 비밀입니다. 처음엔 마법처럼 보여도, 결국 컴파일러가 보이지 않는 곳에서 더 많은 일을 해 주는 것뿐입니다.

또 하나 눈에 띄는 점은 생성된 클래스가 `final`이라는 것입니다. `data class`는 다른 클래스를 상속할 수는 있어도 **다른 클래스에게 상속될 수는 없습니다**. 상속 계층에서 `equals()`/`hashCode()`의 대칭성·일관성을 컴파일러가 안전하게 보장하기 어렵기 때문입니다. 이 제약을 완화하려는 [KEEP 제안(data class inheritance)](https://github.com/Kotlin/KEEP/blob/master/proposals/data-class-inheritance.md)이 논의되고 있지만, `componentN()` 재정의와 생성자 매개변수 관리 등 풀어야 할 과제가 남아 있습니다.

## Pro Tips {#pro-tips}

### private 생성자와 copy()의 가시성 {#copy-visibility}

지금까지는 `private` 생성자로 data class를 만들어도 자동 생성된 `copy()`가 그 가시성을 물려받지 않았습니다. 그래서 팩토리 함수로 생성 규칙을 강제하려 해도, 외부에서 `copy()`를 호출해 검증을 우회한 인스턴스를 만들 수 있는 허점이 있었습니다.

```kotlin
// Kotlin 2.0.20에서 copy() 호출 시 경고 발생
data class PositiveInteger private constructor(val number: Int) {
    companion object {
        fun create(number: Int): PositiveInteger? =
            if (number > 0) PositiveInteger(number) else null
    }
}

fun main() {
    val positive = PositiveInteger.create(42) ?: return
    val broken = positive.copy(number = -1) // 뒷문: 음수 인스턴스가 만들어진다
}
```

향후 Kotlin 릴리스에서는 `copy()`의 기본 가시성이 **생성자의 가시성과 일치**하도록 바뀝니다. 다만 영향 범위가 커서 급격히 적용하지 않고 점진적으로 도입되며, Kotlin 2.0.20부터는 위처럼 영향을 받는 코드에 미리 경고를 띄웁니다. 마이그레이션을 위해 다음 수단이 제공됩니다.

- **`@ConsistentCopyVisibility`** — 기본값이 되기 전에 새 동작(생성자 가시성 = `copy()` 가시성)을 미리 선택한다.
- **`@ExposedCopyVisibility`** — 새 동작을 선택 해제하고 선언부 경고를 무시한다(호출부 경고는 남는다).
- **`-Xconsistent-data-class-copy-visibility`** 컴파일러 옵션 — 모듈 전체의 모든 data class에 새 동작을 일괄 적용한다.

## 요약 {#summary}

> **TL;DR** — `data class`는 데이터를 담는 데 특화된 클래스로, 컴파일러가 `equals()`·`hashCode()`·`toString()`·`copy()`·`componentN()`을 자동 생성합니다. 그래서 `==`는 참조가 아닌 **내용**을 비교하고, 구조 분해와 불변 갱신이 가능해집니다. 다만 이 함수들은 **주 생성자 프로퍼티만** 대상으로 하고 `copy()`는 얕은 복사라는 점에 주의해야 합니다. 일반 클래스는 이런 메서드를 기본 제공하지 않는 대신 동작·로직을 담는 데 더 유연합니다.

1. **자동 생성 5종**: `equals()`(구조적 동등성), `hashCode()`, `toString()`, `copy()`, `componentN()`을 컴파일러가 만들어 준다.
2. **조건**: 주 생성자에 `val`/`var` 프로퍼티가 최소 하나 있어야 하고, `abstract`·`open`·`sealed`·`inner`일 수 없다.
3. **일반 class와의 차이**: 일반 클래스의 `==`는 참조 비교라 값이 같아도 `false`지만, data class는 내용 비교라 `true`다. 구조 분해와 `copy()`도 data class에만 있다.
4. **주의점**: 자동 생성 함수는 주 생성자 프로퍼티만 본다(본문 프로퍼티 제외). 구조 분해는 이름이 아닌 순서를 따르고, `copy()`는 얕은 복사다.
5. **정체**: `data`는 마법이 아니라, 컴파일 시점에 관련 메서드를 바이트코드로 생성하라는 컴파일러 지시일 뿐이다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) data class를 선언하면 컴파일러가 무엇을 생성하나요?">

주 생성자 프로퍼티를 기반으로 다섯 가지를 자동 생성합니다. 구조적 동등성을 비교하는 `equals()`, 그와 일관된 `hashCode()`, 읽기 좋은 `toString()`, 일부 프로퍼티만 바꿔 새 인스턴스를 만드는 `copy()`, 그리고 구조 분해를 지원하는 `component1()`·`component2()`… 입니다. 덕분에 일반 클래스라면 손으로 써야 할 보일러플레이트가 사라집니다.

</def>
<def title="Q) 일반 class와 data class의 == 동작은 어떻게 다른가요?">

일반 클래스는 `equals()`를 재정의하지 않으면 `Any`의 기본 구현, 즉 **참조 동등성**을 씁니다. 그래서 프로퍼티 값이 같아도 서로 다른 객체면 `==`가 `false`입니다. 반면 data class는 컴파일러가 **구조적 동등성** `equals()`를 생성하므로, 주 생성자 프로퍼티 값이 모두 같으면 `==`가 `true`가 됩니다.

</def>
<def title="Q) data class가 되기 위한 조건은 무엇인가요?">

주 생성자에 최소 하나의 매개변수가 있어야 하고, 그 매개변수들은 모두 `val` 또는 `var`로 선언돼야 합니다. 또한 `abstract`, `open`, `sealed`, `inner` 클래스는 data class가 될 수 없습니다. 이 제약들은 컴파일러가 프로퍼티 기반 함수(`equals()` 등)를 안전하게 생성하기 위한 전제입니다.

</def>
<def title="Q) 자동 생성 함수가 본문(body) 프로퍼티를 무시한다는 게 무슨 뜻인가요?">

`equals()`·`hashCode()`·`toString()`·`copy()`는 오직 **주 생성자에 선언된 프로퍼티**만 사용합니다. 클래스 본문에서 `var age = 0`처럼 따로 선언한 프로퍼티는 이 함수들의 대상에서 빠집니다. 그 결과 본문 프로퍼티 값이 서로 달라도 주 생성자 프로퍼티만 같으면 `==`가 `true`가 되고, `toString()`에도 나타나지 않습니다. 따라서 동등성 비교에 참여해야 하는 값은 반드시 주 생성자에 두어야 합니다.

</def>
<def title="Q) copy()가 불변성 관점에서 논쟁이 되는 이유는 무엇인가요?">

`copy()`는 불변 객체를 다룰 때 기존 상태에서 일부만 바꾼 새 인스턴스를 쉽게 파생시켜 주는 편리한 함수입니다. 다만 "완전한 불변이라면 값을 바꿀 통로 자체가 없어야 한다"는 관점에서 보면, 프로퍼티 값을 바꿔 새 인스턴스를 만드는 `copy()`가 불변의 순수성을 다소 퇴색시킨다고 볼 수도 있습니다. 또한 `copy()`는 얕은 복사라, 가변 객체를 프로퍼티로 품고 있으면 원본과 복사본이 그 객체를 공유하는 함정도 있습니다. 편의와 순수성 사이의 트레이드오프입니다.

</def>
</deflist>
</content>
