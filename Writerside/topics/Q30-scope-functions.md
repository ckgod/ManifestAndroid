# Q30) 스코프 함수

스코프 함수는 객체 하나를 잠깐 붙잡아 두고 그 객체를 대상으로 코드 블록을 실행하는 함수입니다. 블록 안에서는 그 객체를 짧은 이름(`this` 또는 `it`)으로 부를 수 있어서, 같은 변수 이름을 반복하지 않고 초기화·변환·로깅 같은 작업을 한 덩어리로 묶을 수 있습니다. 표준 라이브러리에는 `let`, `run`, `with`, `apply`, `also` 다섯 개가 있습니다.

다섯 함수가 하는 일은 사실상 같습니다. 블록을 한 번 실행하는 것이 전부입니다. 차이는 두 가지뿐입니다.

| 함수 | 블록 안에서 객체를 부르는 이름 | 돌려주는 값 | 호출 형태 |
|---|---|---|---|
| `let` | `it` (람다 파라미터) | 블록의 마지막 값 | `obj.let { }` |
| `run` | `this` (수신 객체) | 블록의 마지막 값 | `obj.run { }` |
| `with` | `this` (수신 객체) | 블록의 마지막 값 | `with(obj) { }` |
| `apply` | `this` (수신 객체) | 객체 자신 | `obj.apply { }` |
| `also` | `it` (람다 파라미터) | 객체 자신 | `obj.also { }` |

첫째는 블록 안에서 객체를 `this`로 부르느냐 `it`으로 부르느냐이고, 둘째는 블록의 결과를 돌려주느냐 객체 자신을 돌려주느냐입니다. 이 두 가지만 기억하면 나머지는 구현을 보면 바로 이해됩니다. 아래 코드는 kotlin-stdlib 2.4.21 소스(`Standard.kt`) 기준입니다.

## this 와 it 의 차이 {#this-vs-it}

블록 안에서 객체를 부르는 이름은 블록의 **함수 타입**이 정합니다.

- `(T) -> R` — 객체를 람다의 **파라미터**로 받습니다. 이름을 따로 짓지 않으면 `it`이 됩니다. `let`, `also`가 이 모양입니다.
- `T.() -> R` — 객체를 람다의 **수신 객체**로 받습니다. 블록 안에서 객체가 `this`가 되므로 `this.`를 생략하고 멤버 이름만 써도 됩니다. `run`, `with`, `apply`가 이 모양입니다.

`T.() -> R`은 Q23에서 본 수신 객체 지정 람다입니다. 객체의 멤버를 여러 번 부르거나 속성을 설정할 때는 `this` 쪽이 짧고, 객체를 다른 함수의 인자로 넘기거나 블록 안에서 바깥 `this`와 헷갈리지 않아야 할 때는 `it` 쪽이 읽기 쉽습니다.

## let {#let}

```kotlin
// Standard.kt (kotlin-stdlib 2.4.21)
@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T, R> T.let(block: (T) -> R): R {
    contract {
        callsInPlace(block, InvocationKind.EXACTLY_ONCE)
    }
    return block(this)
}
```

모든 타입 `T`에 붙는 확장 함수입니다. 자기 자신(`this`)을 블록에 인자로 넘기고, 블록이 돌려준 값을 그대로 돌려줍니다. 그래서 블록 안에서는 객체가 `it`이고, 결과는 블록의 마지막 값입니다.

가장 흔한 쓰임은 안전 호출 `?.`과 함께 null이 아닐 때만 무언가를 하는 것입니다.

```kotlin
// LetExample.kt
val name: String? = "skydoves"
val message = name?.let { "Hello, $it!" }
println(message)   // Hello, skydoves!
```

`name`이 null이면 `?.`에서 바로 null이 되고 블록은 실행되지 않습니다. null이 아니면 블록이 실행되며, 이때 `it`의 타입은 `String?`이 아니라 `String`입니다. 안전 호출은 수신 객체가 null이 아닐 때만 함수를 부르므로, 컴파일러가 `T`를 null이 아닌 `String`으로 정하기 때문입니다.

## run {#run}

`run`은 두 가지가 있습니다.

```kotlin
// Standard.kt (kotlin-stdlib 2.4.21)
@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T, R> T.run(block: T.() -> R): R {
    contract {
        callsInPlace(block, InvocationKind.EXACTLY_ONCE)
    }
    return block()
}

@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <R> run(block: () -> R): R {
    contract {
        callsInPlace(block, InvocationKind.EXACTLY_ONCE)
    }
    return block()
}
```

첫 번째는 확장 함수입니다. `let`과 같이 블록의 결과를 돌려주지만, 블록이 수신 객체 지정 람다(`T.() -> R`)라서 블록 안에서 객체가 `this`입니다. 객체의 멤버를 써서 값을 하나 계산할 때 어울립니다.

```kotlin
// RunExample.kt
val isLong = "Welcome to Kotlin".run {
    length > 10   // this.length
}
println(isLong)   // true
```

두 번째는 확장 함수가 아닌 `run`입니다. 대상 객체 없이 블록 하나를 실행하고 결과를 돌려줍니다. 여러 줄의 계산을 식 하나로 묶어 변수에 바로 넣고 싶을 때 씁니다.

```kotlin
// RunBlock.kt
val port = run {
    val env = System.getenv("PORT")
    env?.toIntOrNull() ?: 8080
}
```

## with {#with}

```kotlin
// Standard.kt (kotlin-stdlib 2.4.21)
@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T, R> with(receiver: T, block: T.() -> R): R {
    contract {
        callsInPlace(block, InvocationKind.EXACTLY_ONCE)
    }
    return receiver.block()
}
```

`with`만 확장 함수가 아닙니다. 대상 객체를 첫 번째 인자로 받고, 그 객체를 수신 객체로 삼아 블록을 실행합니다. 하는 일은 확장 함수 `run`과 같고 부르는 모양만 다릅니다. `obj.run { }`은 `with(obj) { }`와 같은 결과를 냅니다.

```kotlin
// WithExample.kt
val developer = StringBuilder("skydoves")
with(developer) {
    append(" - Android Developer")
    println(toString())   // skydoves - Android Developer
}
```

확장 함수가 아니므로 `?.`을 붙일 수 없습니다. 대상이 null일 수 있으면 `obj?.run { }`을 씁니다.

## apply {#apply}

```kotlin
// Standard.kt (kotlin-stdlib 2.4.21)
@kotlin.internal.InlineOnly
@IgnorableReturnValue
public inline fun <T> T.apply(block: T.() -> Unit): T {
    contract {
        callsInPlace(block, InvocationKind.EXACTLY_ONCE)
    }
    block()
    return this
}
```

블록은 수신 객체 지정 람다라서 객체가 `this`이고, 블록이 끝나면 블록의 결과가 아니라 **객체 자신**을 돌려줍니다. 블록의 반환 타입이 `Unit`인 것도 이 때문입니다. 블록은 값을 만들어 내는 곳이 아니라 객체의 속성을 채우는 곳입니다.

그래서 객체를 만들자마자 설정하고 그대로 변수에 담을 때 씁니다.

```kotlin
// ApplyExample.kt
val developer = StringBuilder("skydoves").apply {
    append(" - Android Developer")
}
println(developer)   // skydoves - Android Developer
```

## also {#also}

```kotlin
// Standard.kt (kotlin-stdlib 2.4.21)
@kotlin.internal.InlineOnly
@SinceKotlin("1.1")
@IgnorableReturnValue
public inline fun <T> T.also(block: (T) -> Unit): T {
    contract {
        callsInPlace(block, InvocationKind.EXACTLY_ONCE)
    }
    block(this)
    return this
}
```

`apply`처럼 객체 자신을 돌려주지만, 블록이 객체를 파라미터로 받으므로 블록 안에서는 `it`입니다. 객체를 바꾸는 것보다 객체를 **들여다보는** 일, 즉 로그를 남기거나 값을 검사하는 일에 어울립니다. 체인 중간에 끼워 넣어도 흐름이 바뀌지 않습니다.

```kotlin
// AlsoExample.kt
val name = "skydoves".also {
    println("Logging: $it")
}
println(name)
// Logging: skydoves
// skydoves
```

`also` 블록이 먼저 실행되어 로그가 찍히고, `name`에는 원래 문자열이 그대로 들어갑니다.

## takeIf 와 takeUnless {#take-if}

같은 파일에 스코프 함수와 함께 쓰이는 짝이 하나 더 있습니다.

```kotlin
// Standard.kt (kotlin-stdlib 2.4.21)
@kotlin.internal.InlineOnly
@SinceKotlin("1.1")
public inline fun <T> T.takeIf(predicate: (T) -> Boolean): T? {
    contract {
        callsInPlace(predicate, InvocationKind.EXACTLY_ONCE)
    }
    return if (predicate(this)) this else null
}
```

조건이 참이면 객체 자신을, 거짓이면 null을 돌려줍니다. `takeUnless`는 조건을 뒤집은 버전입니다. 결과가 null일 수 있으므로 보통 `?.let`과 이어서 씁니다.

```kotlin
// TakeIfExample.kt
val input = "  kotlin  "
input.trim().takeIf { it.isNotEmpty() }?.let { println("입력: $it") }
```

## inline 으로 얻는 것 {#inline}

다섯 함수는 모두 `inline` 함수입니다. Q16에서 본 것처럼 컴파일러는 호출하는 자리에 함수 본문과 람다 본문을 그대로 펼쳐 넣습니다. 그래서 스코프 함수를 써도 함수 호출 비용이나 람다 객체를 만드는 비용이 없습니다.

람다가 바깥 변수를 붙잡아(캡처해) 써도 마찬가지입니다.

```kotlin
// CaptureDemo.kt
fun captureDemo(prefix: String): String {
    val count = 3
    return "kotlin".let { "$prefix-$it-$count" }
}
```

이 코드를 컴파일하면 `MainKt.class` 하나만 생기고, `captureDemo`의 바이트코드에는 `let` 호출 없이 `StringBuilder`로 문자열을 이어 붙이는 명령만 남습니다. 펼쳐 넣은 람다 본문이 `prefix`와 `count`를 그냥 지역 변수처럼 읽기 때문에 캡처를 위한 객체가 따로 필요 없습니다. 람다가 캡처하면 익명 클래스가 생길 수 있다는 설명은 `inline`이 아닌 함수에 넘기는 람다에 해당합니다.

## contract 와 callsInPlace {#contract}

다섯 함수 모두 본문 첫머리에 `contract { callsInPlace(block, InvocationKind.EXACTLY_ONCE) }`가 있습니다. 컨트랙트는 함수가 어떻게 동작하는지를 컴파일러에 미리 알려 주는 선언입니다. 이 선언은 "`block`은 이 함수 안에서, 정확히 한 번 실행된다"는 뜻입니다.

컴파일러는 보통 람다가 언제, 몇 번 실행될지 모릅니다. 함수를 호출하는 쪽을 검사할 때 받는 함수의 시그니처만 보고 본문은 보지 않기 때문입니다. `(block: () -> Unit)`이라는 같은 시그니처로 아래 세 가지가 모두 가능합니다.

```kotlin
// UnknownInvocation.kt
import kotlin.random.Random

fun maybe(block: () -> Unit) {
    if (Random.nextBoolean()) block()   // 한 번도 실행되지 않을 수 있습니다
}

fun twice(block: () -> Unit) {
    block(); block()                    // 여러 번 실행될 수 있습니다
}

var saved: (() -> Unit)? = null
fun later(block: () -> Unit) {
    saved = block                       // 함수가 끝난 뒤에 실행될 수 있습니다
}
```

`inline` 함수도 마찬가지입니다. `inline`은 호출 비용을 없애기 위한 것이고, 컴파일러가 변수가 초기화됐는지 검사할 때는 펼쳐질 본문을 보지 않습니다. 그래서 컴파일러는 세 경우를 모두 염두에 두고 검사합니다. 컨트랙트가 있으면 그 가정을 풀 수 있어서, 아래처럼 람다 안에서 `val`을 초기화하는 코드가 컴파일됩니다.

```kotlin
// ValInit.kt
fun valInit(): Int {
    val x: Int
    run { x = 10 }   // 정확히 한 번 실행되므로 초기화로 인정됩니다
    return x
}
```

같은 모양의 `inline` 함수를 컨트랙트 없이 직접 만들어 쓰면 컴파일되지 않습니다.

```kotlin
// NoContract.kt
inline fun <R> myRun(block: () -> R): R = block()

fun valInitNoContract(): Int {
    val x: Int
    myRun { x = 10 }   // error: 'val' cannot be reassigned.
    return x           // error: variable 'x' must be initialized.
}
```

두 오류는 앞의 세 경우에서 나옵니다. 람다가 여러 번 실행될 수 있으면 `val`에 두 번 대입될 수 있고(첫 번째 오류), 한 번도 실행되지 않으면 `x`가 초기화되지 않은 채 읽힐 수 있습니다(두 번째 오류). `inline`이 아닌 함수에 넘긴 람다는 함수가 끝난 뒤에 실행될 수도 있어서, 같은 코드에 "captured values cannot be initialized because of possible reassignments." 오류가 납니다.

`InvocationKind`는 네 가지이고, 무엇을 보장하느냐에 따라 람다 안에서 허용되는 초기화가 다릅니다.

| 종류 | 보장하는 것 | 람다 안에서 초기화 |
|---|---|---|
| `EXACTLY_ONCE` | 정확히 한 번 실행 | `val`을 초기화하고 뒤에서 읽을 수 있습니다 |
| `AT_LEAST_ONCE` | 한 번 이상 실행 | `var`만 초기화된 것으로 인정합니다. `val`은 두 번 대입될 수 있어 오류입니다 |
| `AT_MOST_ONCE` | 많아야 한 번 실행 | `val`에 대입은 할 수 있지만, 실행되지 않았을 수 있어 뒤에서 읽으면 오류입니다 |
| `UNKNOWN` | 함수 안에서 실행된다는 것만 보장 (횟수는 모름) | `val` 초기화는 오류입니다 |

스코프 함수는 모두 `EXACTLY_ONCE`입니다.

컴파일러는 컨트랙트를 믿고 검사를 풀어 주는 것이라, 선언이 틀리면 잘못된 코드가 그대로 실행됩니다. `EXACTLY_ONCE`라고 선언해 놓고 본문에서 람다를 두 번 부르면, Kotlin 2.4.21은 "wrong invocation kind" 경고만 내고 컴파일합니다. 이 함수에 `val`을 초기화하는 람다를 넘기면 실제로 두 번 대입됩니다. 이 경고는 본문만 봐도 횟수가 드러나는 경우에만 나오므로, 경고가 없다고 컨트랙트가 맞다는 뜻은 아닙니다.

`name?.let { it.length }`에서 `it`이 null이 아닌 것으로 취급되는 것은 컨트랙트 덕분이 아닙니다. 앞에서 본 것처럼 `?.`이 null이 아닐 때만 `let`을 부르기 때문이며, 컨트랙트가 없는 자작 `let`으로 바꿔도 똑같이 컴파일됩니다.

직접 만든 함수에 컨트랙트를 쓰려면 Kotlin 2.4.21에서도 `@OptIn(ExperimentalContracts::class)`가 필요합니다. 아직 실험 기능이라 표준 라이브러리는 쓰지만 일반 코드에서는 명시적으로 동의해야 합니다.

## 선언에 붙은 어노테이션 {#annotations}

stdlib 선언에는 책의 발췌에 없는 어노테이션이 두 개 더 붙어 있습니다.

- `@kotlin.internal.InlineOnly` — 인라인으로만 쓰이는 함수라는 표시입니다. 바이트코드에서 `StandardKt__StandardKt`의 `let`, `run`, `apply` 등은 모두 `private static`으로 들어가 있어서, 자바 코드에서는 이 함수들을 부를 수 없습니다. 코틀린에서는 어차피 호출 자리에 펼쳐지므로 문제가 없습니다.
- `@IgnorableReturnValue` — Kotlin 2.2부터 있는 어노테이션으로, 반환값을 쓰지 않아도 경고하지 않는다는 표시입니다. 컴파일러의 반환값 검사 기능(아직 실험 기능)을 켜면 쓰지 않은 반환값에 경고가 나는데, `apply`나 `also`처럼 결과를 버리는 것이 자연스러운 호출은 이 경고에서 빠집니다. `takeIf`·`takeUnless`에는 붙어 있지 않습니다. 결과를 버리면 조건을 검사한 의미가 없으니 경고 대상으로 남겨 둔 것으로 보입니다.

## 고르는 기준 {#choosing}

정답이 하나로 정해져 있지는 않지만, 공식 문서와 흔한 관례는 다음과 같습니다.

| 하고 싶은 일 | 함수 |
|---|---|
| null이 아닐 때만 실행하거나, 값을 다른 값으로 바꿀 때 | `?.let` |
| 객체의 멤버로 값을 하나 계산할 때 | `run` |
| 이미 있는 객체의 메서드를 여러 번 부를 때 (결과는 필요 없음) | `with` |
| 객체를 만들면서 속성을 설정할 때 | `apply` |
| 객체는 그대로 두고 로그·검사를 끼워 넣을 때 | `also` |

표의 각 줄을 예제로 보면 다음과 같습니다.

**`?.let` — null이 아닐 때만 값을 바꿉니다.** 이름이 null이면 블록을 건너뛰고 `?:` 오른쪽의 0이 쓰입니다.

```kotlin
// ChooseLet.kt
fun nameLength(name: String?): Int = name?.let { it.trim().length } ?: 0

println(nameLength("  kotlin "))   // 6
println(nameLength(null))          // 0
```

**`run` — 객체의 멤버로 값을 하나 계산합니다.** 블록 안에서 `this`가 `rect`라서 `width`, `height`를 이름만으로 씁니다.

```kotlin
// ChooseRun.kt
data class Rect(val width: Int, val height: Int)

val rect = Rect(3, 4)
val summary = rect.run { "넓이 ${width * height}, 둘레 ${2 * (width + height)}" }
println(summary)   // 넓이 12, 둘레 14
```

**`with` — 이미 있는 객체의 멤버를 여러 번 씁니다.** 결과를 받지 않고 블록 안의 일만 합니다.

```kotlin
// ChooseWith.kt
data class Config(val host: String, val port: Int)

val config = Config("localhost", 8080)
with(config) {
    println("host = $host")   // host = localhost
    println("port = $port")   // port = 8080
}
```

**`apply` — 객체를 만들면서 속성을 설정합니다.** 블록이 끝나면 설정이 끝난 객체 자신이 `user`에 들어갑니다.

```kotlin
// ChooseApply.kt
class User {
    var name = ""
    var age = 0
}

val user = User().apply {
    name = "kotlin"
    age = 15
}
println("${user.name} ${user.age}")   // kotlin 15
```

**`also` — 체인 중간에 로그를 끼워 넣습니다.** `also`는 받은 리스트를 그대로 돌려주므로 `sorted`에는 정렬된 리스트가 그대로 들어갑니다.

```kotlin
// ChooseAlso.kt
val sorted = listOf(3, 1, 2).sorted()
    .also { println("정렬 결과: $it") }   // 정렬 결과: [1, 2, 3]
println(sorted.first())                 // 1
```

판단이 어려우면 앞의 두 가지 질문으로 돌아가면 됩니다. 블록이 끝난 뒤 필요한 것이 객체 자신이면 `apply`·`also`, 계산 결과면 `let`·`run`·`with`입니다. 블록 안에서 멤버를 많이 부르면 `this` 쪽, 객체를 인자로 넘기거나 이름을 붙이고 싶으면 `it` 쪽입니다.

## 주의할 점 {#pitfalls}

**`?.let { } ?: 기본값` 패턴.** 이 패턴을 if-else처럼 쓰면, 블록이 null을 돌려줄 때도 `?:` 오른쪽이 실행됩니다.

```kotlin
// ElvisPitfall.kt
fun elvisPitfall(v: String?): String =
    v?.let { if (it.isEmpty()) null else it.uppercase() } ?: "default"

println(elvisPitfall(""))     // default  ← v 는 null 이 아닌데도
println(elvisPitfall("ab"))   // AB
```

`v`가 null인 경우와 블록 결과가 null인 경우를 구분해야 하면 `if (v != null) ... else ...`로 쓰는 편이 안전합니다.

**중첩하면 `this`와 `it`이 가려집니다.** `apply` 안에서 다시 `apply`를 쓰면 안쪽 블록의 `this`는 안쪽 객체이고, 바깥 객체의 같은 이름 멤버는 가려집니다. `let` 안의 `let`도 안쪽 `it`이 바깥 `it`을 가립니다. 중첩이 필요하면 `let { user -> ... }`처럼 이름을 붙이거나 `this@라벨`로 어느 객체인지 밝힙니다.

**길게 이어 붙이면 읽기 어렵습니다.** 스코프 함수는 코드를 줄이려고 쓰는 것이지만, 여러 개를 체인으로 잇거나 블록이 길어지면 지금 `this`와 `it`이 무엇인지 따라가기 어려워집니다. 그럴 때는 지역 변수에 담아 평범하게 쓰는 편이 낫습니다.

## 요약 {#summary}

스코프 함수 다섯 개는 모두 블록을 정확히 한 번 실행하는 `inline` 함수이고, 두 가지만 다릅니다. 블록 안에서 객체를 `this`(수신 객체 지정 람다 `T.() -> R`)로 부르느냐 `it`(파라미터 `(T) -> R`)으로 부르느냐, 그리고 블록의 결과를 돌려주느냐(`let`·`run`·`with`) 객체 자신을 돌려주느냐(`apply`·`also`)입니다. `with`만 확장 함수가 아니고, 대상 없이 블록만 실행하는 `run`도 따로 있습니다.

`inline`이라 람다가 바깥 변수를 캡처해도 람다 객체가 만들어지지 않습니다. `callsInPlace(EXACTLY_ONCE)` 컨트랙트 덕분에 블록 안에서 `val`을 초기화할 수 있고, `?.let` 안에서 `it`이 null이 아닌 것은 안전 호출 덕분입니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) let 과 run 은 둘 다 블록의 결과를 돌려주는데 무엇이 다른가요?">

블록 안에서 객체를 부르는 방법이 다릅니다. `let`의 블록 타입은 `(T) -> R`이라 객체가 람다의 파라미터로 들어오고 `it`으로 부릅니다. `run`의 블록 타입은 `T.() -> R`인 수신 객체 지정 람다라 객체가 `this`가 되고 멤버 이름만 써도 됩니다.

그래서 객체를 다른 함수에 인자로 넘기거나 null 처리와 함께 값을 바꿀 때는 `?.let`, 객체의 멤버를 여러 번 써서 값을 하나 계산할 때는 `run`이 자연스럽습니다.

</def>
<def title="Q) apply 와 also 는 각각 언제 쓰나요?">

둘 다 블록을 실행한 뒤 객체 자신을 돌려줍니다. `apply`는 블록 안에서 객체가 `this`라서 `name = "..."`처럼 속성을 바로 설정할 수 있습니다. 객체를 만들면서 설정하는 데 씁니다.

`also`는 블록 안에서 객체가 `it`이라 객체를 들여다보는 일에 어울립니다. 로그를 남기거나 값을 검사하는 코드를 체인 중간에 끼워 넣어도 흐름이 바뀌지 않습니다.

</def>
<def title="Q) 스코프 함수에 넘긴 람다가 바깥 변수를 캡처하면 객체가 만들어지나요?">

만들어지지 않습니다. 스코프 함수는 모두 `inline`이라 컴파일러가 함수 본문과 람다 본문을 호출하는 자리에 펼쳐 넣습니다. 펼쳐진 코드는 바깥 변수를 일반 지역 변수처럼 바로 읽으므로 캡처를 위한 객체가 필요 없습니다.

실제로 `"kotlin".let { "$prefix-$it-$count" }`를 컴파일하면 람다용 클래스는 생기지 않고, 바이트코드에는 `StringBuilder`로 문자열을 잇는 명령만 남습니다.

</def>
<def title="Q) 스코프 함수의 contract { callsInPlace(...) } 는 무슨 역할을 하나요?">

블록이 이 함수 안에서 정확히 한 번 실행된다는 사실을 컴파일러에 알려 줍니다. 컴파일러는 보통 람다가 나중에 실행되거나 여러 번 실행될 수 있다고 가정하는데, 이 선언이 있으면 그 가정을 풀 수 있습니다.

그 결과 `val x: Int; run { x = 10 }`처럼 람다 안에서 `val`을 초기화하는 코드가 컴파일됩니다. 같은 모양의 함수를 컨트랙트 없이 만들면 "'val' cannot be reassigned" 오류가 납니다. 직접 만든 함수에 컨트랙트를 쓰려면 아직 `@OptIn(ExperimentalContracts::class)`가 필요합니다.

</def>
<def title="Q) x?.let { ... } ?: y 를 if-else 대신 쓰면 어떤 문제가 있나요?">

`?:`는 왼쪽 결과가 null이면 오른쪽을 실행합니다. `let`은 블록의 결과를 돌려주므로, `x`가 null이 아니어도 블록이 null을 돌려주면 `y` 쪽이 실행됩니다.

예를 들어 `v?.let { if (it.isEmpty()) null else it.uppercase() } ?: "default"`에 빈 문자열을 넣으면 `v`가 null이 아닌데도 `"default"`가 나옵니다. 두 경우를 구분해야 하면 `if (x != null) ... else ...`로 쓰는 편이 안전합니다.

</def>
</deflist>
