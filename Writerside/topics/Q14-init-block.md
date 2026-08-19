# Q14) init 블록은 언제 호출되며 주요 특징은 무엇인가

`init` 블록은 인스턴스가 만들어질 때 실행되는 초기화 코드입니다. **주 생성자의 인자가 전달된 뒤, 그 인스턴스를 쓰기 시작하기 전에** 실행됩니다.

```kotlin
class User(val name: String, val age: Int) {
    val isAdult: Boolean

    init {
        isAdult = age >= 18
        println("$name / $age / $isAdult")
    }
}

User("John", 20)   // John / 20 / true
```

생성자 인자에 기대는 초기화, 즉 "받은 값으로 계산해서 다른 프로퍼티를 채우는" 일을 담는 자리입니다. 프로퍼티 선언부의 `=` 한 줄로는 표현하기 어려운 로직이 여기에 들어갑니다.

## 실행 순서 — 프로퍼티 초기화자와 섞인다 {#order}

가장 많이 틀리는 지점입니다. "프로퍼티가 먼저 다 초기화되고 그다음 `init`이 돈다"고 알고 있는 경우가 많은데, **정확하지 않습니다.**

클래스 본문의 프로퍼티 초기화자와 `init` 블록은 **소스에 적힌 순서 그대로 번갈아 실행됩니다.**

```kotlin
class Order(val name: String) {
    val a = log("prop a")
    init { log("init 1") }
    val b = log("prop b")
    init { log("init 2") }
}
```

```
prop a
init 1
prop b
init 2
```

`init` 블록 두 개가 연달아 나오는 게 아니라 선언 위치를 따라갑니다. 그래서 **아직 선언되지 않은 아래쪽 프로퍼티를 위쪽 `init`에서 읽으면 컴파일 오류**가 납니다.

```kotlin
class Broken {
    init { println(later) }   // error
    val later = 1
}
```

```
error: variable 'later' must be initialized
```

"주 생성자 프로퍼티가 먼저"라는 설명이 맞는 부분은 **주 생성자 괄호 안에 선언한 프로퍼티**(`val name`)에 한합니다. 그건 본문보다 먼저 대입됩니다. 본문에 쓴 프로퍼티는 해당하지 않습니다.

## 보조 생성자와의 순서 {#secondary}

보조 생성자가 있어도 `init`은 건너뛰어지지 않습니다. 보조 생성자는 주 생성자에 위임해야 하고, 그 위임 과정에서 `init`이 먼저 돌기 때문입니다.

```kotlin
class Order(val name: String) {
    val a = log("prop a")
    init { log("init 1") }
    constructor() : this("default") { log("secondary body") }
}

Order()
```

```
prop a
init 1
secondary body
```

**`init`이 먼저, 보조 생성자 본문이 나중입니다.** 어떤 생성자로 만들든 `init`은 반드시 실행된다는 뜻이고, 이게 `init`을 쓰는 이유이기도 합니다. 보조 생성자가 여러 개여도 초기화 코드를 한 곳에만 두면 됩니다.

## init에서 lateinit은 읽을 수 없다 {#lateinit}

`lateinit` 프로퍼티는 이름 그대로 나중에 대입됩니다. `init` 시점에는 값이 없습니다.

```kotlin
class User(val name: String) {
    lateinit var pref: String
    init {
        println(pref)   // 컴파일은 통과
    }
}
```

```
UninitializedPropertyAccessException
```

**컴파일러가 막아 주지 않습니다.** 실행하는 순간 터집니다. Q12에서 본 대로 `lateinit`의 검사는 읽는 지점에 삽입되는 런타임 검사이고, `init` 안이라고 예외가 아닙니다.

## Pro Tips {#pro-tips}

### init 블록은 바이트코드에 존재하지 않는다 {#bytecode}

`init`이라는 별도의 메서드가 생기지 않습니다. 컴파일러가 **블록의 코드를 생성자 안에 그대로 복사해 넣습니다.**

```kotlin
class User(val username: String) {
    val createdAt: Long
    init {
        require(username.isNotBlank())
        createdAt = System.currentTimeMillis()
    }
}
```

디컴파일하면 이렇게 됩니다.

```java
public final class User {
    private final String username;
    private final long createdAt;

    public User(String username) {
        super();
        this.username = username;
        // ↓ init 블록 코드가 여기에 그대로 들어온다
        if (StringsKt.isBlank(username)) {
            throw new IllegalArgumentException("Failed requirement.");
        }
        this.createdAt = System.currentTimeMillis();
    }
}
```

`init` 블록이 여러 개면 **여러 개가 순서대로 이어 붙습니다.** 보조 생성자가 있으면 그 생성자는 `this(...)`로 주 생성자를 부르므로, 결과적으로 모든 생성 경로에서 같은 코드가 실행됩니다.

Kotlin이 새 문법을 추가하면서도 JVM 호환을 유지하는 전형적인 방식입니다. 언어 차원의 개념을 만들되 바이트코드에는 새 구조를 만들지 않습니다.

### init 블록의 진짜 문제는 실행 시점을 못 미룬다는 것 {#drawbacks}

`init`은 객체가 만들어질 때마다 **무조건, 즉시** 실행됩니다. 늦출 방법이 없습니다. 여기서 문제가 파생됩니다.

- **사이드 이펙트** — 네트워크 호출이나 파일 I/O를 넣으면 객체를 만드는 것만으로 그 일이 벌어집니다. DI 컨테이너가 인스턴스를 미리 만들어 두는 경우처럼, 개발자가 예상하지 못한 시점에 실행될 수 있습니다.
- **성능** — 무거운 연산이 있으면 객체 생성 비용이 그만큼 커집니다. 짧은 간격으로 여러 개 만들면 누적됩니다.
- **디버깅** — 생성자 안에서 터지므로 스택 트레이스가 호출부를 가리키지 않고 객체 생성 지점을 가리킵니다. 원인을 찾기 번거롭습니다.
- **테스트** — 초기화 로직이 생성자 인자에 강하게 묶여, 그 부분만 떼어 검증하기 어려워집니다.

그래서 실무 기준은 단순합니다. **`init`에는 받은 인자로 값을 계산하는 일만 둡니다.** 그 이상이 필요하면 팩토리 함수나 `by lazy`로 뺍니다.

```kotlin
// 이 정도가 적당
init { isAdult = age >= 18 }

// 이건 팩토리로
companion object {
    suspend fun create(id: String): User = User(id, fetchProfile(id))
}
```

`require`나 `check`로 인자를 검증하는 것은 예외입니다. 잘못된 상태의 객체가 만들어지는 것을 막는 일이라 오히려 `init`에 있어야 맞습니다.

## 요약 {#summary}

> **TL;DR** — `init` 블록은 주 생성자 인자가 전달된 뒤 실행되는 초기화 코드입니다. 클래스 본문의 프로퍼티 초기화자와 **선언 순서대로 번갈아** 실행되며, 보조 생성자를 쓰더라도 위임을 통해 항상 먼저 실행됩니다. 바이트코드에는 별도 메서드가 생기지 않고 생성자 안에 그대로 인라인됩니다. 실행 시점을 미룰 수 없으므로 사이드 이펙트나 무거운 연산은 두지 않습니다.

1. **실행 시점**: 주 생성자 인자 전달 후, 인스턴스 사용 전.
2. **순서**: 프로퍼티 초기화자와 `init`이 **소스 순서대로 인터리브**된다. "프로퍼티 먼저, init 나중"은 주 생성자 괄호 안 프로퍼티에만 해당.
3. **아래쪽 프로퍼티 참조 불가**: 위쪽 `init`에서 아래 프로퍼티를 읽으면 컴파일 오류.
4. **보조 생성자**: `init`이 먼저, 보조 생성자 본문이 나중. 모든 생성 경로에서 실행 보장.
5. **`lateinit` 접근 불가**: 컴파일은 통과하고 실행 시 `UninitializedPropertyAccessException`.
6. **바이트코드**: 별도 메서드 없음. 생성자에 그대로 복사됨. 여러 개면 순서대로 이어 붙음.
7. **쓰는 기준**: 인자로 값을 계산하는 일과 `require`/`check` 검증까지. 그 이상은 팩토리나 `by lazy`로.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) init 블록은 정확히 언제 실행되나요?">

주 생성자의 인자가 전달된 직후, 그 인스턴스를 사용하기 전에 실행됩니다. 더 정확히는 클래스 본문에 있는 프로퍼티 초기화자와 함께 **소스 코드에 적힌 순서대로** 실행됩니다. `init` 블록이 두 개면 각각 자기 위치에서 실행되고, 사이에 프로퍼티 선언이 있으면 그 초기화가 중간에 끼어듭니다. 흔히 "프로퍼티가 전부 초기화된 다음 init이 돈다"고 설명하는데, 그 설명이 맞는 것은 주 생성자 괄호 안에 선언한 프로퍼티에 한합니다.

</def>
<def title="Q) init 블록과 보조 생성자 본문 중 무엇이 먼저 실행되나요?">

`init` 블록이 먼저입니다. 보조 생성자는 주 생성자에 직접 또는 간접적으로 위임해야 하는데, 그 위임 호출(`this(...)`)이 처리되는 과정에서 `init` 블록이 실행되고, 그다음에 보조 생성자의 본문이 실행됩니다. 덕분에 어떤 생성자로 객체를 만들든 `init`은 항상 실행되며, 보조 생성자가 여러 개여도 공통 초기화 코드를 `init`에 한 번만 쓰면 됩니다.

</def>
<def title="Q) init 블록 안에서 lateinit 프로퍼티를 쓸 수 있나요?">

읽을 수 없습니다. `lateinit`은 정의상 나중에 대입되는 프로퍼티라 `init` 시점에는 값이 없습니다. 문제는 **컴파일러가 이를 막아 주지 않는다**는 점입니다. 컴파일은 통과하고 실행하는 순간 `UninitializedPropertyAccessException`이 발생합니다. `lateinit`의 초기화 검사는 컴파일 타임 검사가 아니라 읽는 지점에 삽입되는 런타임 null 검사이기 때문이며, `init` 블록 안이라고 예외가 적용되지 않습니다.

</def>
<def title="Q) init 블록은 바이트코드에서 어떻게 표현되나요?">

별도의 메서드로 만들어지지 않습니다. 컴파일러가 `init` 블록의 코드를 **생성자 본문에 그대로 복사해 넣습니다.** 디컴파일해 보면 슈퍼클래스 생성자 호출과 주 생성자 프로퍼티 대입 다음에 `init` 블록의 코드가 이어져 있습니다. `init` 블록이 여러 개면 선언 순서대로 이어 붙고, 보조 생성자가 있으면 그 생성자는 주 생성자에 위임하므로 결과적으로 모든 생성 경로에서 같은 초기화 코드가 실행됩니다. 새 언어 개념을 추가하면서도 JVM 바이트코드에는 새 구조를 만들지 않는 Kotlin의 전형적인 방식입니다.

</def>
<def title="Q) init 블록에 어떤 코드를 두면 안 되나요?">

실행 시점을 미룰 수 없다는 점에서 문제가 파생됩니다. 네트워크 호출이나 파일 I/O 같은 사이드 이펙트를 넣으면 객체를 만드는 것만으로 그 일이 벌어지며, DI 컨테이너가 인스턴스를 미리 생성하는 경우처럼 예상하지 못한 시점에 실행될 수 있습니다. 무거운 연산은 객체 생성 비용을 키우고, 생성자 안에서 예외가 나면 스택 트레이스가 객체 생성 지점을 가리켜 원인 추적이 번거로워집니다. 기준은 "받은 인자로 값을 계산하는 일"까지이며, `require`/`check` 검증은 잘못된 상태의 객체가 만들어지는 것을 막는 일이라 오히려 `init`에 두는 것이 맞습니다. 그 이상이 필요하면 팩토리 함수나 `by lazy`로 뺍니다.

</def>
</deflist>
