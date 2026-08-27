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

Java 8의 람다와 같은 방식이고, Kotlin은 JVM 타겟 1.8 이상에서 이걸 기본으로 씁니다. 람다마다 생기던 클래스 파일이 없어지므로 JVM에서는 클래스 수와 로딩 비용이 줄어듭니다. 안드로이드는 사정이 다른데, 아래에서 따로 다룹니다.

> 값을 캡처하지 않는 람다는 인스턴스가 한 번만 만들어져 재사용됩니다. 매 호출마다 객체가 생기지 않습니다. 다만 이건 `invokedynamic`이 가져온 이점이 아닙니다. 익명 클래스 시절에도 kotlinc가 `INSTANCE` 필드에 싱글턴을 넣어 두었습니다.

### 익명 클래스 방식과의 비교 {#vs-anonymous-class}

`invokedynamic`이 바꾼 것은 **인스턴스가 생기느냐**가 아니라 **그 인스턴스의 클래스를 누가 언제 만드느냐**입니다. 두 방식 모두 `Function1` 구현체가 힙에 하나 필요합니다. 인스턴스가 아예 없어지는 것은 `inline`뿐입니다.

호출 지점의 명령만 비교하면 이렇습니다.

| | 익명 클래스 | `invokedynamic` |
|---|---|---|
| 캡처 없음 | `GETSTATIC INSTANCE` | `INVOKEDYNAMIC` |
| 캡처 있음 | `NEW` · `DUP` · 캡처값 로드 · `INVOKESPECIAL` | 캡처값 로드 · `INVOKEDYNAMIC` |

캡처가 없으면 명령 수가 같습니다. 실제로 줄어드는 것은 **클래스 파일 개수**입니다. 익명 클래스 방식은 람다 하나마다 `.class` 파일이 하나씩 생겼고, 그 안에 자체 constant pool과 생성자, `invoke` 브리지 메서드, `kotlin.jvm.internal.Lambda` 상속에 딸린 것들이 모두 들어갔습니다. `invokedynamic`은 이걸 원래 클래스 안의 `private static` 메서드 하나로 대체합니다.

대신 첫 호출에서 `LambdaMetafactory`가 구현체를 만드는 부트스트랩 비용이 붙습니다. **시작 비용만 놓고 보면 `invokedynamic` 쪽이 더 큽니다.** 클래스 수가 줄어드는 이점과 맞바꾸는 것입니다.

그리고 방식을 런타임에 위임한다는 점 자체가 원래 명분이었습니다. 익명 클래스는 "람다는 클래스다"라는 구현 전략을 컴파일 시점에 바이트코드로 확정해 버리지만, `invokedynamic`은 필요한 시그니처만 남기고 만드는 방법은 JVM에 맡깁니다. 더 나은 방식이 나오면 재컴파일 없이 적용됩니다.

### 안드로이드에서의 desugaring {#android-desugaring}

여기까지는 JVM 이야기입니다. **안드로이드에서는 이 최적화가 그대로 유지되지 않습니다.**

D8이 빌드 과정에서 `invokedynamic`을 다시 synthetic 클래스로 되돌립니다. 크래시 스택 트레이스에서 보이는 `$$ExternalSyntheticLambda`가 그 결과물입니다.

`minSdk`를 26 이상으로 올려도 마찬가지입니다. ART가 `invoke-custom` 바이트코드 자체는 읽을 수 있지만, 런타임에 구현체를 만들어 주는 `LambdaMetafactory`가 안드로이드 런타임에 구현되어 있지 않기 때문입니다. 만들어 줄 주체가 없으니 컴파일 시점에 만들어 두는 수밖에 없습니다.

따라서 최종 DEX에는 람다마다 클래스가 다시 생깁니다. **클래스 파일이 줄어든다는 이점은 JVM에 해당하고 APK에는 적용되지 않습니다.** R8이 인라인하거나 병합해 없애는 경우는 별개입니다.

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

> **TL;DR** — 고차 함수는 함수를 인자로 받거나 반환하는 함수입니다. 바이트코드에서는 `FunctionN` 인터페이스로 표현되고, 람다는 익명 클래스가 아니라 **`invokedynamic` + `private static` 메서드**로 컴파일됩니다. `inline`을 붙이면 그 인스턴스 생성과 호출마저 사라지고 람다 본문이 호출부에 펼쳐집니다. 다만 안드로이드에서는 D8이 `invokedynamic`을 다시 클래스로 되돌립니다.

1. **정의**: 함수를 인자로 받거나, 반환하거나, 둘 다 하는 함수.
2. **함수 타입 표기**: `(입력) -> 반환`. 바이트코드에서는 `Function0`~`Function22`.
3. **장점**: 핵심 흐름과 달라지는 동작을 분리해 재사용성이 오르고, 의도가 함수 이름에 드러나 가독성이 좋아진다.
4. **람다 컴파일**: 익명 클래스가 아니다. 본문은 `private static` 메서드로 빠지고 `invokedynamic`으로 인스턴스를 얻는다. "익명 클래스로 컴파일된다"는 설명은 옛 정보.
5. **캡처 없는 람다**: 인스턴스가 한 번만 생성되어 재사용된다. 익명 클래스 시절에도 `INSTANCE` 싱글턴으로 같았으므로 `invokedynamic`의 새 이점은 아니다.
6. **인스턴스 생성 자체**: 두 방식 모두 `Function1` 구현체가 필요하다. `invokedynamic`이 바꾼 것은 그 클래스를 **누가 언제 만드느냐**이며, 대신 첫 호출에 부트스트랩 비용이 붙는다.
7. **안드로이드 예외**: D8이 `invokedynamic`을 `$$ExternalSyntheticLambda` 클래스로 되돌린다. `minSdk` 26 이상도 마찬가지이므로 클래스 수 이점은 APK에 적용되지 않는다.
8. **`inline`**: `invokedynamic`·`invokestatic` 모두 사라지고 람다 본문이 호출부에 인라인된다. 표준 라이브러리 컬렉션 함수가 전부 `inline`인 이유.
9. **인라인의 대가**: 호출부마다 코드가 복사되어 바이트코드가 커진다 (Q16으로 이어짐).

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 고차 함수란 무엇인가요?">

다른 함수를 매개변수로 받거나, 함수를 반환하거나, 둘 다 하는 함수입니다. 함수를 값처럼 다룰 수 있다는 뜻이며, 함수 타입은 `(입력타입) -> 반환타입`으로 표기합니다. `map`·`filter`·`reduce` 같은 컬렉션 연산과 콜백이 모두 고차 함수로 구현되어 있습니다. 핵심 흐름은 함수가 갖고 달라지는 동작만 밖에서 주입하는 구조라, 같은 구조를 여러 상황에 재사용할 수 있고 무엇을 하는 코드인지가 함수 이름에 드러납니다.

</def>
<def title="Q) 함수 타입은 JVM 바이트코드에서 어떻게 표현되나요?">

JVM에는 함수 타입이라는 개념이 없어서, Kotlin 표준 라이브러리의 `FunctionN` 인터페이스로 치환됩니다. 매개변수가 없으면 `Function0<R>`, 하나면 `Function1<P, R>`, 둘이면 `Function2<P1, P2, R>` 식이며 `kotlin.jvm.functions` 패키지에 `Function0`부터 `Function22`까지 정의되어 있습니다. 따라서 `fun higherOrder(op: (Int) -> Int)`는 `Function1`을 받는 메서드가 되고, 함수 호출은 `op.invoke(10)`이 됩니다. 인터페이스 하나로 바뀌는 것뿐이라 특별한 런타임 지원이 필요하지 않습니다.

</def>
<def title="Q) 람다는 익명 클래스로 컴파일되나요?">

현재 컴파일러는 그렇게 하지 않습니다. kotlinc 2.2.20으로 확인해 보면 익명 클래스 파일이 아예 생성되지 않습니다. 람다 본문은 `private static` 메서드(`useNormal$lambda$0` 같은 이름)로 추출되고, 함수 인스턴스는 `invokedynamic` 명령으로 얻습니다. JVM의 `LambdaMetafactory`가 런타임에 구현체를 만들어 주는 방식이며 Java 8 람다와 동일합니다. Kotlin은 JVM 타겟 1.8 이상에서 이를 기본으로 사용하고, 람다마다 생기던 클래스 파일이 없어져 JVM에서는 클래스 수와 로딩 비용이 줄어듭니다. 다만 안드로이드에서는 D8이 이를 다시 클래스로 되돌리므로 APK에는 이 이점이 적용되지 않습니다. "람다는 익명 클래스가 된다"고 설명하는 자료는 옛 컴파일러 기준입니다.

</def>
<def title="Q) inline을 붙이면 바이트코드가 어떻게 달라지나요?">

함수 인스턴스 생성과 호출이 모두 사라집니다. 일반 고차 함수는 `invokedynamic`으로 `Function1` 인스턴스를 만들고 `invokestatic`으로 함수를 호출하는데, `inline`을 붙이면 두 명령이 모두 없어지고 람다 본문이 호출 지점에 그대로 펼쳐집니다. 함수 호출 자체가 없어지는 것입니다. `map`·`filter`·`forEach` 같은 표준 라이브러리 컬렉션 함수가 전부 `inline`인 이유가 이것으로, 반복문 안에서 람다를 호출하는 구조라 효과가 큽니다. 다만 호출부마다 코드가 복사되므로 함수가 크거나 호출 지점이 많으면 바이트코드 크기가 늘어난다는 대가가 있습니다.

</def>
<def title="Q) 고차 함수를 쓰면 항상 객체가 생성되나요?">

아닙니다. 두 가지 경우에 생성되지 않습니다. 첫째로 `inline` 함수라면 람다 본문이 호출부에 인라인되므로 인스턴스 자체가 만들어지지 않습니다. 둘째로 인라인이 아니더라도 **값을 캡처하지 않는 람다**는 인스턴스가 한 번만 생성되어 재사용되므로 호출할 때마다 새로 만들어지지 않습니다. 이는 `invokedynamic` 고유의 이점이 아니라 익명 클래스 방식에서도 `INSTANCE` 싱글턴으로 동일했습니다. 객체가 매번 생성되는 것은 바깥 변수를 캡처하는 람다를 인라인이 아닌 고차 함수에 넘길 때이며, 캡처한 값을 담아야 하므로 인스턴스가 따로 필요합니다.

</def>
<def title="Q) invokedynamic으로 바뀌면서 실제로 줄어든 것은 무엇인가요?">

명령 수가 아니라 **클래스 파일 개수**입니다. 익명 클래스 방식은 람다 하나마다 `.class` 파일이 하나씩 생겼고 그 안에 자체 constant pool, 생성자, `invoke` 브리지 메서드가 모두 들어갔는데, `invokedynamic`은 이를 원래 클래스 안의 `private static` 메서드 하나로 대체합니다. 호출 지점만 비교하면 캡처가 없을 때는 양쪽 다 명령 하나로 같고, 캡처가 있을 때만 `NEW`·`DUP`·`INVOKESPECIAL` 세 단계가 `INVOKEDYNAMIC` 하나로 줄어듭니다. 인스턴스가 생성된다는 사실 자체는 달라지지 않으며, 바뀐 것은 그 클래스를 컴파일러가 미리 만드느냐 `LambdaMetafactory`가 런타임에 만드느냐입니다. 그 대가로 첫 호출에 부트스트랩 비용이 붙어 시작 비용은 오히려 커집니다.

</def>
<def title="Q) 안드로이드에서도 람다가 invokedynamic으로 남나요?">

남지 않습니다. D8이 빌드 과정에서 `invokedynamic`을 다시 synthetic 클래스로 되돌리며, 크래시 스택 트레이스에 찍히는 `$$ExternalSyntheticLambda`가 그 결과물입니다. `minSdk`를 26 이상으로 올려도 마찬가지인데, ART가 `invoke-custom` 바이트코드 자체는 읽을 수 있지만 런타임에 구현체를 만들어 주는 `LambdaMetafactory`가 안드로이드 런타임에 구현되어 있지 않기 때문입니다. 만들어 줄 주체가 없으니 컴파일 시점에 만들어 두는 수밖에 없습니다. 따라서 최종 DEX에는 람다마다 클래스가 다시 생기고, "클래스 파일이 줄어든다"는 이점은 JVM에만 해당합니다.

</def>
</deflist>
