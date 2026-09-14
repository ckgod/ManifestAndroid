# Q23) DSL 과 타입 안전 빌더

DSL(Domain-Specific Language)은 **특정 영역의 문제를 그 영역의 말투로 적게 해 주는 API 설계 방식**입니다. 코틀린에서는 별도의 파서나 언어를 만들지 않고 평범한 함수와 람다만으로 이런 문법을 만들 수 있습니다.

```kotlin
val user = user {
    name = "Alice"
    age = 28
}
```

설정 파일처럼 보이지만 전부 코틀린 코드입니다. 오타가 나면 컴파일되지 않고, IDE 자동완성도 그대로 동작합니다. 그래서 **타입 안전 빌더**(type-safe builder)라고도 부릅니다.

Gradle의 `build.gradle.kts`, Jetpack Compose의 `Column { }`, Ktor의 라우팅이 모두 이 방식입니다.

## 수신 객체 지정 람다 {#lambda-with-receiver}

DSL을 떠받치는 핵심 장치는 하나입니다. **람다에 수신 객체를 붙이는 것**입니다.

Q18에서 본 일반 람다의 타입은 `(User) -> Unit`이었습니다. 여기에 수신 객체를 붙이면 `User.() -> Unit`이 됩니다.

```kotlin
val a: (User) -> Unit = { u -> u.name = "Alice" }   // 파라미터로 받는다
val b: User.() -> Unit = { name = "Alice" }         // this가 된다
```

차이는 **람다 안에서 `User`가 `this`가 된다**는 것입니다. `this`는 생략할 수 있으므로 `name = "Alice"`처럼 클래스 안에 있는 것처럼 쓸 수 있습니다. DSL이 설정 블록처럼 읽히는 이유가 전부 여기서 나옵니다.

Q20의 확장 함수가 수신 객체를 첫 파라미터로 받는 정적 메서드였던 것과 같은 구조입니다. 확장 함수가 **선언**에 수신 객체를 붙인 것이라면, 수신 객체 지정 람다는 **람다 타입**에 붙인 것입니다.

## 빌더 만들기 {#builder}

이 하나만 있으면 빌더가 완성됩니다.

```kotlin
data class User(
    var name: String = "",
    var age: Int = 0
)

fun user(block: User.() -> Unit): User = User().apply(block)
```

`user` 함수가 하는 일은 세 가지입니다. 빈 `User`를 만들고, 넘겨받은 블록을 그 객체를 수신 객체로 삼아 실행하고, 객체를 돌려줍니다. `apply`가 정확히 그 일을 하므로 한 줄이면 됩니다.

호출부는 이렇게 됩니다.

```kotlin
val user = user {
    name = "Alice"
    age = 28
}
println(user)   // User(name=Alice, age=28)
```

프로퍼티가 `var`이고 기본값이 있어야 합니다. 블록 안에서 대입으로 값을 채우는 구조이고, 채우지 않은 프로퍼티는 기본값으로 남아야 하기 때문입니다.

## 중첩 구조 {#nesting}

DSL의 진가는 구조가 겹칠 때 나옵니다. 각 계층마다 클래스를 두고, 그 클래스의 메서드가 다시 수신 객체 지정 람다를 받게 하면 트리가 됩니다.

```kotlin
class Html {
    private val elements = mutableListOf<String>()

    fun body(init: Body.() -> Unit) {
        val body = Body()
        body.init()
        elements.add(body.toString())
    }

    override fun toString() = elements.joinToString("\n", "<html>\n", "\n</html>")
}

class Body {
    private val elements = mutableListOf<String>()

    fun h1(text: String) { elements.add("<h1>$text</h1>") }
    fun p(text: String) { elements.add("<p>$text</p>") }

    override fun toString() = elements.joinToString("\n", "<body>\n", "\n</body>")
}

fun html(init: Html.() -> Unit): String = Html().apply(init).toString()
```

쓰는 쪽은 HTML 자체와 거의 같은 모양이 됩니다.

```kotlin
val content = html {
    body {
        h1("Hello, Kotlin DSL!")
        p("This is a simple HTML builder example.")
    }
}
```

```
<html>
<body>
<h1>Hello, Kotlin DSL!</h1>
<p>This is a simple HTML builder example.</p>
</body>
</html>
```

`body` 블록 안에서 `h1`과 `p`만 보이는 이유는 그 블록의 수신 객체가 `Body`이기 때문입니다. **어떤 위치에서 무엇을 쓸 수 있는지를 타입이 강제합니다.** `html { h1("x") }`처럼 잘못된 위치에 쓰면 컴파일되지 않습니다.

## 스코프가 새는 문제 {#scope-leak}

여기까지만 만들면 구멍이 하나 남습니다. **중첩된 안쪽 블록에서 바깥 수신 객체가 그대로 보입니다.**

```kotlin
html {
    body {
        h1("정상")
        body { h1("바깥 Html.body 를 Body 안에서 호출") }
    }
}
```

`body` 안에서 다시 `body`를 부르고 있습니다. 논리적으로 말이 안 되는데 **컴파일도 실행도 됩니다.** kotlinc 2.2.21로 확인했습니다.

```
<h1>정상</h1>
<h1>바깥 Html.body 를 Body 안에서 호출</h1>
```

안쪽 람다에서 `Body`를 못 찾으면 컴파일러가 바깥으로 올라가 `Html`에서 찾기 때문입니다. 암시적 수신 객체가 여러 겹 쌓이면 안쪽에서 바깥 것까지 전부 접근할 수 있습니다.

DSL이 깊어질수록 이 구멍이 위험해집니다. 사용자는 자기가 어느 계층에 있는지 착각한 채 엉뚱한 함수를 부르고, 컴파일러는 막아 주지 않습니다.

## DslMarker {#dsl-marker}

`@DslMarker`가 이 문제를 해결합니다. 어노테이션을 하나 만들어 표시를 달고, 그 표시가 붙은 클래스들을 계층으로 묶습니다.

```kotlin
@DslMarker
annotation class HtmlDsl

@HtmlDsl class Html { fun body(init: Body.() -> Unit) { ... } }
@HtmlDsl class Body { fun h1(text: String) { ... } }
```

같은 마커가 붙은 수신 객체가 여럿 겹치면 **가장 안쪽 것만 암시적으로 쓸 수 있게** 됩니다. 아까 그 코드가 이제 막힙니다.

```
error: 'fun body(init: Body.() -> Unit): Unit' cannot be called in this context
       with an implicit receiver. Use an explicit receiver if necessary.
```

오류 메시지가 해법까지 알려 줍니다. 정말로 바깥 것을 불러야 한다면 `this@html.body { }`처럼 명시적으로 적으면 됩니다. **실수는 막고 의도는 열어 두는** 설계입니다.

DSL을 만든다면 `@DslMarker`는 선택이 아니라 기본입니다.

## 장단점 {#pros-cons}

**장점**

1. **가독성** — 설정과 구조를 선언적으로 적어 의도가 그대로 드러납니다.
2. **타입 안전성** — 위치마다 쓸 수 있는 것이 타입으로 제한되고, 오타는 컴파일 오류가 됩니다. 자동완성도 동작합니다.
3. **유연성** — 선택적 프로퍼티를 기본값으로 두면 생성자 오버로드나 별도 빌더 클래스가 필요 없습니다.

**단점**

1. **구현 비용** — 계층마다 클래스와 함수를 만들어야 해서, 쓰는 쪽이 짧아지는 대신 만드는 쪽이 길어집니다.
2. **학습 곡선** — 쓰는 사람이 어떤 블록에서 무엇이 가능한지 따로 익혀야 합니다. 문서가 없으면 자동완성에 의존하게 됩니다.
3. **디버깅** — 람다가 여러 겹 중첩되어 스택 트레이스가 길고 읽기 어렵습니다.

한 번 쓰고 말 객체 생성에는 과합니다. **같은 구조를 여러 곳에서 반복해 만들 때** 값을 합니다.

## 요약 {#summary}

> **TL;DR** — DSL은 수신 객체 지정 람다(`T.() -> Unit`)로 만듭니다. 람다 안에서 대상이 `this`가 되므로 설정 블록처럼 읽히고, 계층마다 클래스를 두면 위치별로 쓸 수 있는 것이 타입으로 강제됩니다. 다만 그대로 두면 안쪽에서 바깥 수신 객체가 보이므로 `@DslMarker`로 막아야 합니다.

1. **정체**: 특정 영역의 문법처럼 읽히는 API. 별도 언어가 아니라 평범한 코틀린 코드다.
2. **핵심 장치**: 수신 객체 지정 람다 `T.() -> Unit`. 람다 안에서 `T`가 `this`가 되어 `this`를 생략할 수 있다.
3. **빌더 공식**: 객체를 만들고 `apply(block)`으로 블록을 적용한 뒤 돌려준다. 프로퍼티는 `var` + 기본값.
4. **중첩**: 계층마다 클래스를 두고 그 메서드가 다시 수신 객체 지정 람다를 받게 한다. 위치별 사용 가능 범위가 타입으로 강제된다.
5. **스코프 누수**: 기본 상태에서는 안쪽 블록에서 바깥 수신 객체가 보인다. `body` 안에서 `body`를 부르는 코드가 컴파일된다.
6. **`@DslMarker`**: 같은 마커가 붙은 수신 객체 중 가장 안쪽만 암시적으로 쓸 수 있게 제한한다. 필요하면 `this@html`로 명시 호출.
7. **기준**: 같은 구조를 반복해 만들 때 값을 한다. 일회성 객체 생성에는 과하다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) DSL 이란 무엇이며 코틀린에서 어떻게 만드나요?">

특정 문제 영역에 맞춘 문법처럼 읽히는 API를 말합니다. 코틀린에서는 별도의 언어나 파서 없이 평범한 함수와 람다만으로 만들 수 있어 타입 안전 빌더라고도 부릅니다. 핵심 장치는 수신 객체 지정 람다인 `T.() -> Unit`입니다. 이 타입의 람다는 안에서 `T`가 `this`가 되고 `this`를 생략할 수 있어, 대상 클래스 안에 있는 것처럼 프로퍼티를 대입하고 메서드를 부를 수 있습니다. 여기에 확장 함수, 기본 인자를 곁들이면 `user { name = "Alice" }` 같은 선언적 문법이 만들어집니다. Gradle의 `build.gradle.kts`, Compose의 `Column { }`이 같은 방식입니다.

</def>
<def title="Q) 수신 객체 지정 람다는 일반 람다와 무엇이 다른가요?">

대상을 파라미터로 받느냐 `this`로 받느냐가 다릅니다. `(User) -> Unit`은 `{ u -> u.name = "Alice" }`처럼 인자로 받아 매번 이름을 통해 접근해야 하지만, `User.() -> Unit`은 `{ name = "Alice" }`처럼 `this`가 되어 생략할 수 있습니다. 이 차이가 DSL이 설정 블록처럼 읽히게 만드는 전부입니다. 구조로 보면 확장 함수와 같습니다. 확장 함수가 선언에 수신 객체를 붙인 것이라면, 수신 객체 지정 람다는 람다 타입에 붙인 것입니다.

</def>
<def title="Q) DSL 에서 스코프가 샌다는 것은 무슨 뜻인가요?">

중첩된 안쪽 블록에서 바깥 블록의 수신 객체까지 그대로 보이는 현상입니다. 안쪽 람다에서 이름을 찾지 못하면 컴파일러가 바깥 수신 객체로 올라가 탐색하기 때문에, 암시적 수신 객체가 여러 겹 쌓이면 안쪽에서 바깥 함수를 부를 수 있게 됩니다. 예를 들어 HTML 빌더에서 `body { body { ... } }`처럼 논리적으로 말이 안 되는 코드가 컴파일도 실행도 됩니다. DSL이 깊어질수록 사용자가 자기 위치를 착각한 채 엉뚱한 함수를 부를 위험이 커집니다.

</def>
<def title="Q) @DslMarker 는 무엇을 하나요?">

같은 마커가 붙은 수신 객체가 여러 겹 중첩되면 가장 안쪽 것만 암시적으로 사용할 수 있도록 제한합니다. `@DslMarker`를 붙인 어노테이션을 하나 만들고 DSL 계층의 클래스들에 그 어노테이션을 달면 됩니다. 그러면 앞서의 `body { body { ... } }`는 "cannot be called in this context with an implicit receiver"라는 컴파일 오류가 납니다. 정말로 바깥 수신 객체를 써야 하는 경우에는 `this@html.body { }`처럼 명시적으로 지정하면 되므로, 실수는 막으면서 의도적인 사용은 열어 두는 구조입니다. DSL을 직접 만든다면 사실상 필수입니다.

</def>
<def title="Q) DSL 의 단점은 무엇인가요?">

첫째, 구현 비용입니다. 계층마다 클래스와 함수를 정의해야 해서 쓰는 쪽이 짧아지는 만큼 만드는 쪽이 길어집니다. 둘째, 학습 곡선입니다. 사용자는 어느 블록에서 무엇을 쓸 수 있는지 따로 익혀야 하고, 문서가 없으면 자동완성에 의존하게 됩니다. 셋째, 디버깅이 어렵습니다. 람다가 여러 겹 중첩되어 스택 트레이스가 길어지고 어느 블록에서 문제가 났는지 파악하기 번거롭습니다. 그래서 한 번 쓰고 마는 객체 생성에는 과하고, 같은 구조를 여러 곳에서 반복해 만들 때 값을 합니다.

</def>
</deflist>
