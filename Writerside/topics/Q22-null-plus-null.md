# Q22) null + null 의 평가 결과

`null + null`은 컴파일 오류도 NPE도 아닙니다. **문자열 `"nullnull"`이 됩니다.**

```kotlin
fun main() {
    val result = null + null
    println(result)                      // nullnull
    println(result::class.simpleName)    // String
}
```

kotlinc 2.2.21로 실제 컴파일해 확인한 결과입니다. 값의 타입도 `java.lang.String`입니다.

산술 연산처럼 보이는 식이 문자열 연산으로 끝났습니다. 이 결과가 어디서 나오는지 따라가 보면 코틀린의 연산자 해석 방식이 드러납니다.

## + 는 함수 호출 {#operator-overloading}

코틀린에서 연산자는 문법에 박힌 기능이 아니라 **약속된 이름의 함수를 부르는 축약**입니다. `a + b`는 `a.plus(b)`로 해석됩니다.

```kotlin
data class Money(val won: Int) {
    operator fun plus(other: Money) = Money(won + other.won)
}

Money(1000) + Money(500)   // Money(won=1500)
```

`operator` 키워드가 붙은 `plus`가 있으면 `+`를 쓸 수 있습니다. 즉 `+`의 의미는 **수신 객체의 타입이 무엇이냐에 따라 달라집니다.**

그래서 `null + null`에서 물어야 할 것은 "null끼리 더하면 얼마인가"가 아니라 **"어떤 `plus` 함수가 선택되는가"** 입니다.

## 선택되는 함수 {#resolution}

표준 라이브러리에 이런 확장 함수가 있습니다.

```kotlin
public operator fun String?.plus(other: Any?): String
```

두 가지가 눈에 띕니다.

- **수신 타입이 `String?`** — nullable이라 `null`을 수신 객체로 받을 수 있습니다.
- **인자 타입이 `Any?`** — 무엇이든 받습니다.

`null` 리터럴의 타입은 `Nothing?`인데, `Nothing?`은 모든 nullable 타입의 하위 타입이므로 `String?` 자리에 들어갑니다. 인자 쪽도 `Any?`라 통과합니다. 후보 중 이 함수만 양쪽을 만족하므로 선택됩니다.

이 함수는 내부적으로 양쪽을 문자열로 바꿔 잇습니다. 그 과정에서 **`null`은 문자열 `"null"`로 변환**됩니다. `println(null)`이 `null`을 출력하는 것과 같은 규칙입니다.

결과적으로 `"null" + "null"`이 되어 `"nullnull"`이 나옵니다.

같은 규칙이 이어집니다.

```kotlin
val s: String? = null
println(s + null)   // nullnull
println(s + 1)      // null1
```

## 산술이 아닌 이유 {#not-arithmetic}

`Int`끼리였다면 이야기가 달라집니다.

```kotlin
val a: Int? = null
val b: Int? = null
println(a + b)
```

```
error: operator call is prohibited on a nullable receiver of type 'Int?'.
       Use '?.'-qualified call instead.
error: argument type mismatch: actual type is 'Int?', but 'Int' was expected.
```

오류가 양쪽에서 납니다. 수신 객체 쪽은 **nullable 수신 객체로 연산자를 부를 수 없다**고 하고, 인자 쪽은 `Int`를 기대했는데 `Int?`가 왔다고 합니다.

`Int.plus`의 시그니처가 `Int.plus(other: Int): Int`이기 때문입니다. 수신 타입도 인자 타입도 non-null이라 양쪽 다 막힙니다. **`String?.plus`처럼 nullable 수신 타입을 가진 산술 연산자가 없습니다.**

즉 `null + null`이 되는 것은 코틀린이 널에 관대해서가 아니라, **하필 문자열 연결 연산자만 nullable 수신 타입으로 선언되어 있기 때문**입니다.

## 설계 의도 {#rationale}

`String?.plus`가 nullable 수신 타입을 갖는 데는 이유가 있습니다. 문자열을 잇는 일은 로그·메시지·UI 텍스트를 만드는 자리에서 끊임없이 일어나는데, 값 하나가 `null`이라는 이유로 앱이 죽으면 곤란합니다.

```kotlin
val nickname: String? = loadNickname()
log("사용자: " + nickname)   // nickname이 null이어도 "사용자: null"
```

문자열 템플릿도 같은 규칙을 따릅니다.

```kotlin
println("값: $nickname")   // 값: null
```

Q0에서 본 코틀린의 널 안전성이 "모든 `null`을 금지한다"가 아니라 **"`null`이 예기치 않게 터지지 않게 한다"** 는 방향임을 보여 주는 사례입니다.

## 실무에서의 함정 {#pitfall}

안전한 대신 **조용합니다.** 버그가 예외가 아니라 잘못된 문자열로 나타납니다.

```kotlin
val userName: String? = null
val greeting = "안녕하세요, " + userName + "님"
println(greeting)   // 안녕하세요, null님
```

크래시가 나지 않으니 개발 중에 놓치기 쉽고, 사용자 화면에 `null`이라는 글자가 그대로 찍힙니다.

의도적으로 다루려면 `null`을 문자열로 흘려보내지 말고 그 자리에서 처리해야 합니다.

```kotlin
val greeting = "안녕하세요, " + (userName ?: "손님") + "님"
println(userName.orEmpty())       // 빈 문자열
println(userName.isNullOrBlank()) // true
```

`orEmpty()`와 `isNullOrBlank()`는 Q20에서 본 **nullable 수신 객체 확장**입니다. `String?.plus`와 같은 계열의 설계입니다.

## 요약 {#summary}

> **TL;DR** — `null + null`은 `"nullnull"`입니다. `+`가 `plus` 함수 호출로 해석되는데, 후보 중 유일하게 nullable 수신 타입을 가진 `String?.plus(Any?)`가 선택되고 그 안에서 `null`이 문자열 `"null"`로 변환되기 때문입니다. 안전하지만 조용해서, 잘못된 값이 예외 대신 `"null"` 이라는 글자로 새어 나갑니다.

1. **결과**: `"nullnull"`, 타입은 `String`. 컴파일 오류도 NPE도 아니다.
2. **연산자의 정체**: `a + b`는 `a.plus(b)`의 축약. `+`의 의미는 수신 객체 타입이 정한다.
3. **선택되는 함수**: `String?.plus(other: Any?): String`. `null` 리터럴의 타입 `Nothing?`이 `String?`에 들어가고 인자는 `Any?`라 통과한다.
4. **변환 규칙**: 문자열 연결 맥락에서 `null`은 `"null"`이 된다. 문자열 템플릿도 동일하다.
5. **산술은 안 된다**: `Int?`끼리 `+`는 컴파일 오류. `Int.plus`의 수신 타입이 non-null이라 후보가 없다.
6. **설계 의도**: 로그·메시지 조립에서 값 하나가 `null`이라고 앱이 죽지 않게 하려는 것.
7. **함정**: 예외가 아니라 잘못된 문자열로 나타나 조용히 지나간다. `?:`·`orEmpty()`로 그 자리에서 처리한다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) null + null 을 실행하면 어떻게 되나요?">

문자열 `"nullnull"`이 됩니다. 컴파일 오류도 `NullPointerException`도 발생하지 않고, 결과 타입은 `String`입니다. 여기서 `+`는 산술 덧셈이 아니라 문자열 연결입니다. 코틀린에서 `a + b`는 `a.plus(b)` 호출로 해석되는데, 후보 중 표준 라이브러리의 `String?.plus(other: Any?): String`만 수신 타입이 nullable이라 `null`을 받을 수 있어 선택됩니다. 그 함수가 양쪽을 문자열로 변환하면서 `null`이 `"null"`이 되고, 둘을 이어 `"nullnull"`이 나옵니다.

</def>
<def title="Q) Int? 끼리 더하면 왜 안 되나요?">

`Int`의 `plus` 연산자는 수신 타입이 non-null인 `Int`라서 `null`을 수신 객체로 받을 수 없기 때문입니다. 적용 가능한 후보가 하나도 없어 컴파일 오류가 납니다. 반대로 `null + null`이 되는 것은 코틀린이 널 연산에 관대해서가 아니라, 문자열 연결 연산자만 예외적으로 nullable 수신 타입으로 선언되어 있기 때문입니다. 즉 이 동작은 널 처리의 일반 규칙이 아니라 특정 표준 라이브러리 함수의 시그니처에서 나오는 결과입니다.

</def>
<def title="Q) 이 동작이 왜 위험할 수 있나요?">

안전한 대신 조용하기 때문입니다. 값이 비어 있다는 사실이 예외로 드러나지 않고 `"null"` 이라는 문자열로 바뀌어 흘러갑니다. `"안녕하세요, " + userName + "님"` 같은 코드는 크래시 없이 `안녕하세요, null님`을 출력하고, 그대로 사용자 화면에 노출됩니다. 개발 중에는 눈에 잘 띄지 않아 배포 후에 발견되기 쉽습니다. 엘비스 연산자로 기본값을 주거나 `orEmpty()`, `isNullOrBlank()` 같은 nullable 수신 객체 확장으로 그 자리에서 처리하는 편이 안전합니다.

</def>
</deflist>
