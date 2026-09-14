# Q21) 구조적 동등성과 참조적 동등성

코틀린은 두 값을 비교하는 방법을 둘로 나눠 둡니다. **내용이 같은가**를 묻는 구조적 동등성(`==`)과, **같은 객체인가**를 묻는 참조적 동등성(`===`)입니다.

```kotlin
data class Person(val name: String)

val p1 = Person("skydoves")
val p2 = Person("skydoves")
val p3 = p1

println(p1 == p2)    // true  — 내용이 같다
println(p1 === p2)   // false — 다른 인스턴스다
println(p1 === p3)   // true  — 같은 인스턴스다
```

`p1`과 `p2`는 내용이 같지만 힙에는 별개의 객체로 앉아 있습니다. 두 질문이 서로 다른 답을 낸다는 것 자체가 둘을 구분해 둔 이유입니다.

## 구조적 동등성 {#structural}

`==`는 내용을 비교하며, **`equals()`의 구현이 그 판정 기준을 정합니다.** `equals()`를 재정의하지 않으면 `Any`의 기본 구현이 쓰이는데, 그건 참조 비교라 `===`와 결과가 같아집니다.

```kotlin
class Plain(val name: String)                 // equals 재정의 없음
data class Data(val name: String)             // equals 자동 생성

println(Plain("a") == Plain("a"))   // false — Any.equals = 참조 비교
println(Data("a") == Data("a"))     // true  — 내용 비교
```

Q2에서 본 대로 `data class`는 주 생성자 프로퍼티를 기준으로 `equals()`와 `hashCode()`를 만들어 줍니다. `==`가 기대대로 동작하는 이유가 그것입니다.

## 참조적 동등성 {#referential}

`===`는 두 참조가 힙의 같은 주소를 가리키는지만 봅니다. **재정의할 수 없고, 재정의할 필요도 없습니다.** 비교 대상이 내용이 아니라 정체성이기 때문입니다.

문자열에서 이 차이가 눈에 띄게 드러납니다.

```kotlin
val s1 = "hello"
val s2 = "hello"
val s3 = StringBuilder("hel").append("lo").toString()

println(s1 === s2)   // true  — 리터럴은 상수 풀에서 공유된다
println(s1 === s3)   // false — 런타임에 새로 만든 객체다
println(s1 == s3)    // true  — 내용은 같다
```

`s1 === s2`가 `true`인 것은 JVM이 문자열 리터럴을 인터닝해 하나로 공유하기 때문입니다. 같은 코드처럼 보여도 만들어진 경로가 다르면 `===`의 답이 달라집니다. **문자열 비교에 `===`를 쓰면 안 되는 이유가 여기 있습니다.**

## == 의 컴파일 결과 {#compilation}

`a == b`는 `a.equals(b)`의 단순한 별칭이 아닙니다. 그렇다면 `a`가 `null`일 때 NPE가 나야 하는데 나지 않습니다.

컴파일러는 이 식을 **의미상** 아래와 같이 다룹니다.

```kotlin
a?.equals(b) ?: (b === null)
```

`a`가 `null`이 아니면 `equals`를 부르고, `null`이면 단락되어 오른쪽으로 넘어가 "`b`도 `null`인가"를 묻습니다. 그래서 `null == null`은 `true`, `null == 어떤값`은 `false`가 됩니다. 네 가지 조합이 전부 안전하게 처리됩니다.

여기서 오른쪽이 `==`가 아니라 `===`인 점을 눈여겨볼 만합니다. `b == null`로 썼다면 그 비교가 다시 `equals`를 부르려 하면서 재귀에 빠질 수 있습니다. 정체성 비교는 어떤 사용자 구현에도 의존하지 않으므로 그 위험이 없습니다.

다만 **실제 바이트코드는 이 식을 그대로 펼쳐 놓지 않습니다.** kotlinc 2.2.21로 확인한 결과입니다.

```kotlin
fun cmpNullable(a: P?, b: P?) = a == b
fun cmpNonNull(a: P, b: P) = a == b
```

```
$ javap -c -p EqKt
  public static final boolean cmpNullable(P, P);
       0: aload_0
       1: aload_1
       2: invokestatic  // Method kotlin/jvm/internal/Intrinsics.areEqual:(Ljava/lang/Object;Ljava/lang/Object;)Z
       5: ireturn
```

호출 한 번으로 끝납니다. `Intrinsics.areEqual`이 위 의미를 내부에 담고 있어, 호출부마다 널 검사 코드를 펼칠 필요가 없습니다. 흥미로운 건 **피연산자가 non-null일 때도 같은 함수를 부른다**는 점입니다.

정리하면 `a?.equals(b) ?: (b === null)`은 **동작을 설명하는 식**이고, 생성되는 코드는 그 동작을 담은 함수 호출 하나입니다.

## 원시 타입에서 갈리는 지점 {#primitives}

`==`가 곧 `equals()`라고 외우면 **원시 타입에서 어긋납니다.** 코틀린의 `Double`, `Int` 같은 타입은 박싱되지 않은 자리에서 JVM 원시 타입으로 컴파일되고, 그때 `==`는 `equals()`가 아니라 기계 수준의 비교가 됩니다.

```kotlin
val d1: Double = 0.0
val d2: Double = -0.0

println(d1 == d2)          // true
println(d1.equals(d2))     // false
```

같은 두 값인데 `==`와 `equals()`의 답이 다릅니다. IEEE 754에서 `0.0`과 `-0.0`은 수치적으로 같지만 비트 표현이 달라서, 원시 비교는 같다고 하고 `Double.equals`는 다르다고 합니다.

`NaN`은 방향이 반대입니다.

```kotlin
val nan = Double.NaN
println(nan == nan)                    // false — IEEE 754 규칙
println(listOf(nan).contains(nan))     // true  — 컬렉션은 equals를 쓴다
```

박싱되는 순간 규칙이 바뀝니다.

```kotlin
val b1: Any = 0.0
val b2: Any = -0.0
println(b1 == b2)   // false — Any로 올라가면서 박싱되어 equals 호출
```

**타입이 `Any`로 올라가거나 컬렉션에 담기는 순간 비교 기준이 달라진다**는 뜻입니다. 부동소수점을 키로 쓰거나 집합에 담을 때 조심해야 하는 이유입니다.

## equals 와 hashCode 의 계약 {#contract}

`equals()`를 재정의하면 `hashCode()`도 함께 재정의해야 합니다. **같다고 판정된 두 객체는 같은 해시를 내야 한다**는 계약이 있고, 해시 기반 컬렉션이 이 계약을 전제로 동작하기 때문입니다.

계약을 어기면 이렇게 됩니다.

```kotlin
class BadEq(val id: Int) {
    override fun equals(other: Any?) = other is BadEq && other.id == id
    // hashCode 재정의 안 함
}

val a = BadEq(1)
val b = BadEq(1)

println(a == b)                      // true
println(a.hashCode() == b.hashCode()) // false
println(hashSetOf(a, b).size)        // 2   ← 같다면서 둘 다 들어간다
println(hashSetOf(a).contains(b))    // false
```

`equals`는 같다고 하는데 `HashSet`은 둘을 다른 것으로 봅니다. 해시가 다르면 **아예 다른 버킷을 뒤지기 때문에** `equals`를 부를 기회조차 없습니다.

`data class`로 선언하면 둘이 함께 생성되므로 이 문제가 나지 않습니다.

```kotlin
data class GoodEq(val id: Int)

println(hashSetOf(GoodEq(1), GoodEq(1)).size)        // 1
println(hashSetOf(GoodEq(1)).contains(GoodEq(1)))    // true
```

## 정체성이 없는 타입 {#no-identity}

`value class`에는 `===`를 쓸 수 없습니다. 컴파일 오류입니다.

```kotlin
@JvmInline value class UserId(val id: String)

val a = UserId("1")
val b = UserId("1")
println(a === b)
// error: identity equality for arguments of types 'UserId' and 'UserId' is prohibited.
```

Q6에서 본 대로 `value class`의 래퍼는 런타임에 소거될 수 있습니다. 소거되고 나면 가리킬 "그 객체"가 아예 없으므로 정체성이라는 개념이 성립하지 않습니다. 언어가 질문 자체를 막아 둔 것입니다.

## 요약 {#summary}

> **TL;DR** — `==`는 내용을, `===`는 정체성을 비교합니다. `==`는 `equals()` 구현에 위임되고 널 안전하게 감싸여 있으며, 실제 바이트코드는 `Intrinsics.areEqual` 호출 하나입니다. 다만 원시 타입 자리에서는 `equals()`가 아니라 기계 비교가 되어 `0.0`·`-0.0`·`NaN`에서 답이 갈립니다.

1. **구조적 동등성 `==`**: 내용 비교. `equals()` 구현이 기준을 정하고, 재정의하지 않으면 참조 비교로 떨어진다.
2. **참조적 동등성 `===`**: 같은 인스턴스인지만 본다. 재정의 불가.
3. **널 안전성**: `a == b`는 의미상 `a?.equals(b) ?: (b === null)`. 네 가지 널 조합이 전부 안전하고 NPE가 나지 않는다.
4. **오른쪽이 `===`인 이유**: `equals` 재귀 호출 위험을 피하려는 것. 정체성 비교는 사용자 구현에 의존하지 않는다.
5. **실제 컴파일 결과**: 위 식을 펼치지 않고 `Intrinsics.areEqual` 한 번을 부른다. 피연산자가 non-null이어도 같다.
6. **원시 타입의 예외**: `0.0 == -0.0`은 `true`인데 `0.0.equals(-0.0)`은 `false`. `NaN == NaN`은 `false`인데 컬렉션의 `contains`는 `true`. 박싱되면 규칙이 바뀐다.
7. **`hashCode` 계약**: `equals`만 재정의하면 해시 기반 컬렉션이 깨진다. 해시가 다르면 다른 버킷이라 `equals`를 부르지도 않는다.
8. **`value class`**: 래퍼가 소거될 수 있어 `===`가 금지되어 있다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 구조적 동등성과 참조적 동등성은 어떻게 다른가요?">

구조적 동등성은 `==`로 두 객체의 내용이 같은지 비교하고, 참조적 동등성은 `===`로 두 참조가 메모리에서 같은 객체를 가리키는지 비교합니다. 구조적 동등성은 `equals()` 구현에 위임되므로 클래스가 재정의한 기준에 따라 결과가 달라지고, `data class`처럼 `equals()`가 자동 생성되면 프로퍼티 값이 같을 때 `true`가 됩니다. 참조적 동등성은 주소를 직접 비교하므로 재정의할 수 없습니다. 내용이 같은 두 인스턴스는 `==`가 `true`, `===`가 `false`인 것이 전형적인 상황입니다.

</def>
<def title="Q) a == b 는 내부적으로 어떻게 동작하나요?">

의미상으로는 `a?.equals(b) ?: (b === null)`로 다뤄집니다. `a`가 `null`이 아니면 `equals`를 호출하고, `null`이면 안전 호출이 단락되어 엘비스 오른쪽으로 넘어가 `b`도 `null`인지 확인합니다. 덕분에 피연산자가 어느 쪽이든 `null`일 수 있어도 NPE가 나지 않고 네 가지 조합이 모두 올바르게 처리됩니다. 오른쪽이 `b == null`이 아니라 `b === null`인 것은 의도적입니다. 정체성 비교는 사용자 정의 `equals` 구현에 의존하지 않아 무한 재귀 위험이 없기 때문입니다. 다만 실제 바이트코드는 이 식을 펼치지 않고 `Intrinsics.areEqual` 호출 하나로 컴파일되며, 이 함수가 같은 의미를 내부에 담고 있습니다.

</def>
<def title="Q) == 는 항상 equals() 를 호출하나요?">

아닙니다. 원시 타입으로 컴파일되는 자리에서는 `equals()`가 아니라 기계 수준의 값 비교가 됩니다. 그래서 `0.0 == -0.0`은 `true`지만 `0.0.equals(-0.0)`은 `false`입니다. IEEE 754에서 두 값은 수치적으로 같으나 비트 표현이 다르기 때문입니다. `NaN`은 반대 방향인데, `nan == nan`은 `false`지만 `listOf(nan).contains(nan)`은 `true`입니다. 컬렉션이 `equals`를 쓰기 때문입니다. 값이 `Any`로 올라가거나 컬렉션에 담겨 박싱되면 비교 기준이 `equals`로 바뀌므로, 부동소수점을 키로 쓰거나 집합에 담을 때 주의해야 합니다.

</def>
<def title="Q) equals() 를 재정의하면 왜 hashCode() 도 재정의해야 하나요?">

같다고 판정된 두 객체는 같은 해시를 내야 한다는 계약이 있고, 해시 기반 컬렉션이 이 계약을 전제로 동작하기 때문입니다. `equals()`만 재정의하면 `a == b`는 `true`인데 두 객체의 해시가 달라져, `HashSet`에 둘 다 들어가고 `contains`도 `false`를 반환합니다. 해시가 다르면 아예 다른 버킷을 탐색하므로 `equals`를 호출할 기회조차 없기 때문입니다. `data class`는 둘을 함께 생성하므로 이 문제가 발생하지 않습니다.

</def>
<def title="Q) 문자열 비교에 === 를 쓰면 안 되는 이유는 무엇인가요?">

문자열 리터럴은 JVM이 상수 풀에 인터닝해 공유하므로 `"hello" === "hello"`가 `true`가 됩니다. 하지만 런타임에 만들어진 문자열은 별도 객체라 내용이 같아도 `===`가 `false`입니다. 즉 같은 값인데도 만들어진 경로에 따라 결과가 달라져 신뢰할 수 없습니다. 내용을 비교할 의도라면 언제나 `==`를 써야 합니다.

</def>
<def title="Q) value class 에 === 를 쓸 수 없는 이유는 무엇인가요?">

`value class`의 래퍼는 컴파일 시점에 소거되어 기반 타입으로 대체될 수 있습니다. 소거된 뒤에는 "이 객체"라고 가리킬 대상 자체가 존재하지 않으므로 정체성이라는 개념이 성립하지 않습니다. 그래서 컴파일러가 `identity equality for arguments of types ... is prohibited` 오류로 질문 자체를 막습니다. 이 제약 덕분에 컴파일러는 박싱과 언박싱을 자유롭게 오가면서도 의미를 깨뜨리지 않을 수 있습니다.

</def>
</deflist>
