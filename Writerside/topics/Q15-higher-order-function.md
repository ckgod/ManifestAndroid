# Q15) 고차 함수와 그 장점

고차 함수는 **함수를 인자로 받거나, 함수를 반환하거나, 둘 다 하는 함수**입니다. 함수를 값처럼 다룰 수 있다는 뜻이고, 이게 Kotlin에서 `map` · `filter` · 콜백 같은 것들이 성립하는 근거입니다.

```kotlin
fun higherOrder(input: Int, op: (Int) -> Int): Int = op(input)

higherOrder(5) { it * 2 }   // 10
```

함수 타입은 `(입력타입) -> 반환타입`으로 씁니다. 위의 `op`는 `Int`를 받아 `Int`를 돌려주는 함수입니다.

## 두 가지 형태 {#forms}

**함수를 받는 쪽**이 흔히 보는 형태입니다.

```kotlin
fun double(x: Int) = x * 2

higherOrder(5, ::double)    // 함수 참조
higherOrder(5) { it * 2 }   // 람다
```

**함수를 돌려주는 쪽**은 상대적으로 덜 쓰이지만, 동작을 골라서 만들어 줄 때 유용합니다.

```kotlin
fun operation(type: String): (Int, Int) -> Int = when (type) {
    "add"      -> { a, b -> a + b }
    "multiply" -> { a, b -> a * b }
    else       -> { _, _ -> 0 }
}

val add = operation("add")
add(3, 4)   // 7
```

## 사용 사례 {#usage}

**컬렉션 연산**이 가장 많이 만나는 사례입니다. `map` · `filter` · `reduce`가 전부 고차 함수입니다.

```kotlin
listOf(1, 2, 3, 4).map { it * 2 }   // [2, 4, 6, 8]
```

루프와 조건문으로 쓰면 "무엇을 하는지"가 코드 사이에 묻히는데, 고차 함수는 의도가 함수 이름에 드러납니다.

**콜백**도 마찬가지입니다.

```kotlin
fun performAction(onComplete: () -> Unit) {
    println("작업 중")
    onComplete()
}

performAction { println("완료") }
```

핵심 흐름은 함수가 갖고, 달라지는 동작만 밖에서 넣습니다. 같은 구조를 여러 상황에 재사용할 수 있게 되는 지점입니다.

## Pro Tips {#pro-tips}

### 함수 타입과 FunctionN 인터페이스 {#function-interface}

JVM에는 "함수 타입"이라는 게 없습니다. 그래서 Kotlin은 표준 라이브러리의 인터페이스로 바꿔 표현합니다.

| Kotlin | 바이트코드 |
|---|---|
| `() -> R` | `Function0<R>` |
| `(P) -> R` | `Function1<P, R>` |
| `(P1, P2) -> R` | `Function2<P1, P2, R>` |

`kotlin.jvm.functions` 패키지에 `Function0`부터 `Function22`까지 정의되어 있습니다.

```kotlin
fun higherOrder(op: (Int) -> Int): Int = op(10)
```

```java
public static final int higherOrder(Function1<? super Integer, Integer> op)
```

호출은 `op.invoke(10)`이 됩니다. `(Int) -> Int`가 인터페이스 하나로 치환되는 것뿐이라, 특별한 런타임 지원이 필요하지 않습니다.

### 람다 컴파일 방식의 변화 {#indy}

오래된 자료는 "람다가 익명 클래스로 컴파일된다"고 설명합니다. **현재 컴파일러는 그렇게 하지 않습니다.**

```kotlin
fun useNormal(): Int = higherOrder { it * 2 }
```

kotlinc 2.2.20으로 컴파일하면 생성되는 클래스 파일이 `HofKt.class` 하나뿐입니다. `HofKt$useNormal$1.class` 같은 익명 클래스가 없습니다.

바이트코드를 보면 이유가 나옵니다.

```
public static final int useNormal();
   0: invokedynamic #57,  0    // InvokeDynamic #0:invoke:()Lkotlin/jvm/functions/Function1;
   5: invokestatic  #59        // Method higherOrder:(Lkotlin/jvm/functions/Function1;)I
   8: ireturn

private static final int useNormal$lambda$0(int);
   0: iload_0
   1: iconst_2
   2: imul
   3: ireturn
```

두 가지가 보입니다.

- **람다 본문은 `private static` 메서드로 추출됩니다** — `useNormal$lambda$0`. 클래스가 아니라 메서드입니다.
- **`invokedynamic`으로 `Function1` 인스턴스를 얻습니다.** JVM의 `LambdaMetafactory`가 런타임에 구현체를 만들어 줍니다.

Java 8의 람다와 같은 방식이고, Kotlin은 JVM 타겟 1.8 이상에서 이걸 기본으로 씁니다. 클래스 파일이 줄어드니 APK 메서드 수와 로딩 비용에도 유리합니다.

> 값을 캡처하지 않는 람다는 `LambdaMetafactory`가 인스턴스를 한 번만 만들어 재사용합니다. 매 호출마다 객체가 생기지 않습니다.

### inline의 최적화 {#inline}

고차 함수를 쓰면 `Function1` 인스턴스를 만들고 `invoke`를 호출하는 비용이 생깁니다. `inline`은 그것마저 없앱니다.

```kotlin
inline fun inlineHigherOrder(op: (Int) -> Int): Int = op(10)

fun useInline(): Int = inlineHigherOrder { it * 2 }
```

```
public static final int useInline();
   2: bipush        10
   4: istore_1
   7: iload_1
   8: iconst_2
   9: imul
```

`invokedynamic`도 `invokestatic`도 없습니다. **람다 본문이 호출 지점에 그대로 펼쳐졌습니다.** 함수 호출 자체가 사라진 것입니다.

앞의 `useNormal`과 비교하면 차이가 분명합니다.

| | `useNormal` | `useInline` |
|---|---|---|
| `Function1` 생성 | `invokedynamic` | 없음 |
| 함수 호출 | `invokestatic` | 없음 |
| 람다 본문 | 별도 메서드 | 호출부에 인라인 |

`map` · `filter` · `forEach` 같은 표준 라이브러리 컬렉션 함수가 전부 `inline`인 이유가 이것입니다. 반복문 안에서 람다를 호출하는 구조라 인라인 효과가 큽니다.

다만 인라인은 공짜가 아닙니다. 호출부마다 코드가 복사되므로 함수가 크거나 호출 지점이 많으면 바이트코드가 불어납니다. 이 트레이드오프는 Q16에서 이어집니다.

## 요약 {#summary}

> **TL;DR** — 고차 함수는 함수를 인자로 받거나 반환하는 함수입니다. 바이트코드에서는 `FunctionN` 인터페이스로 표현되고, 람다는 익명 클래스가 아니라 **`invokedynamic` + `private static` 메서드**로 컴파일됩니다. `inline`을 붙이면 그 인스턴스 생성과 호출마저 사라지고 람다 본문이 호출부에 펼쳐집니다.

1. **정의**: 함수를 인자로 받거나, 반환하거나, 둘 다 하는 함수.
2. **함수 타입 표기**: `(입력) -> 반환`. 바이트코드에서는 `Function0`~`Function22`.
3. **장점**: 핵심 흐름과 달라지는 동작을 분리해 재사용성이 오르고, 의도가 함수 이름에 드러나 가독성이 좋아진다.
4. **람다 컴파일**: 익명 클래스가 아니다. 본문은 `private static` 메서드로 빠지고 `invokedynamic`으로 인스턴스를 얻는다. "익명 클래스로 컴파일된다"는 설명은 옛 정보.
5. **캡처 없는 람다**: 인스턴스가 한 번만 생성되어 재사용된다.
6. **`inline`**: `invokedynamic`·`invokestatic` 모두 사라지고 람다 본문이 호출부에 인라인된다. 표준 라이브러리 컬렉션 함수가 전부 `inline`인 이유.
7. **인라인의 대가**: 호출부마다 코드가 복사되어 바이트코드가 커진다 (Q16으로 이어짐).

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 고차 함수란 무엇인가요?">

다른 함수를 매개변수로 받거나, 함수를 반환하거나, 둘 다 하는 함수입니다. 함수를 값처럼 다룰 수 있다는 뜻이며, 함수 타입은 `(입력타입) -> 반환타입`으로 표기합니다. `map`·`filter`·`reduce` 같은 컬렉션 연산과 콜백이 모두 고차 함수로 구현되어 있습니다. 핵심 흐름은 함수가 갖고 달라지는 동작만 밖에서 주입하는 구조라, 같은 구조를 여러 상황에 재사용할 수 있고 무엇을 하는 코드인지가 함수 이름에 드러납니다.

</def>
<def title="Q) 함수 타입은 JVM 바이트코드에서 어떻게 표현되나요?">

JVM에는 함수 타입이라는 개념이 없어서, Kotlin 표준 라이브러리의 `FunctionN` 인터페이스로 치환됩니다. 매개변수가 없으면 `Function0<R>`, 하나면 `Function1<P, R>`, 둘이면 `Function2<P1, P2, R>` 식이며 `kotlin.jvm.functions` 패키지에 `Function0`부터 `Function22`까지 정의되어 있습니다. 따라서 `fun higherOrder(op: (Int) -> Int)`는 `Function1`을 받는 메서드가 되고, 함수 호출은 `op.invoke(10)`이 됩니다. 인터페이스 하나로 바뀌는 것뿐이라 특별한 런타임 지원이 필요하지 않습니다.

</def>
<def title="Q) 람다는 익명 클래스로 컴파일되나요?">

현재 컴파일러는 그렇게 하지 않습니다. kotlinc 2.2.20으로 확인해 보면 익명 클래스 파일이 아예 생성되지 않습니다. 람다 본문은 `private static` 메서드(`useNormal$lambda$0` 같은 이름)로 추출되고, 함수 인스턴스는 `invokedynamic` 명령으로 얻습니다. JVM의 `LambdaMetafactory`가 런타임에 구현체를 만들어 주는 방식이며 Java 8 람다와 동일합니다. Kotlin은 JVM 타겟 1.8 이상에서 이를 기본으로 사용하고, 클래스 파일 수가 줄어 APK 메서드 수와 클래스 로딩 비용에도 유리합니다. "람다는 익명 클래스가 된다"고 설명하는 자료는 옛 컴파일러 기준입니다.

</def>
<def title="Q) inline을 붙이면 바이트코드가 어떻게 달라지나요?">

함수 인스턴스 생성과 호출이 모두 사라집니다. 일반 고차 함수는 `invokedynamic`으로 `Function1` 인스턴스를 만들고 `invokestatic`으로 함수를 호출하는데, `inline`을 붙이면 두 명령이 모두 없어지고 람다 본문이 호출 지점에 그대로 펼쳐집니다. 함수 호출 자체가 없어지는 것입니다. `map`·`filter`·`forEach` 같은 표준 라이브러리 컬렉션 함수가 전부 `inline`인 이유가 이것으로, 반복문 안에서 람다를 호출하는 구조라 효과가 큽니다. 다만 호출부마다 코드가 복사되므로 함수가 크거나 호출 지점이 많으면 바이트코드 크기가 늘어난다는 대가가 있습니다.

</def>
<def title="Q) 고차 함수를 쓰면 항상 객체가 생성되나요?">

아닙니다. 두 가지 경우에 생성되지 않습니다. 첫째로 `inline` 함수라면 람다 본문이 호출부에 인라인되므로 인스턴스 자체가 만들어지지 않습니다. 둘째로 인라인이 아니더라도 **값을 캡처하지 않는 람다**는 `LambdaMetafactory`가 인스턴스를 한 번만 생성해 재사용하므로 호출할 때마다 새로 만들어지지 않습니다. 객체가 매번 생성되는 것은 바깥 변수를 캡처하는 람다를 인라인이 아닌 고차 함수에 넘길 때이며, 캡처한 값을 담아야 하므로 인스턴스가 따로 필요합니다.

</def>
</deflist>
