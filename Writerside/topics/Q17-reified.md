# Q17) reified 키워드와 그 이점

`reified`는 **인라인 함수 안에서 제네릭 타입을 런타임에 알 수 있게** 해 주는 키워드입니다. 원래 제네릭 타입은 실행 시점에 지워져 있어 `value is T`나 `T::class` 같은 코드를 쓸 수 없는데, `reified`가 그 제약을 풀어 줍니다.

```kotlin
inline fun <reified T> isType(value: Any): Boolean = value is T

isType<String>("Hello")   // true
isType<Int>("Hello")      // false
```

이름은 "구체화하다(reify)"에서 왔습니다. 지워질 타입을 실제 타입으로 되살린다는 뜻입니다.

## 타입 소거 {#type-erasure}

왜 이런 키워드가 필요한지 알려면 먼저 무엇이 지워지는지 봐야 합니다.

JVM은 컴파일이 끝나면 제네릭 타입 정보를 제거합니다. 이것을 타입 소거(type erasure)라고 합니다. 제네릭이 없던 시절의 코드와 호환되도록 도입된 설계입니다.

그래서 `List<String>`과 `List<Int>`는 런타임에 **둘 다 그냥 `List`** 입니다. 소스에서는 분명히 구분되지만 실행 중에는 그 차이가 남아 있지 않습니다.

여기서 막히는 일이 생깁니다.

```kotlin
fun <T> isType(value: Any): Boolean {
    return value is T      // 컴파일 오류
}
```

`T`가 무엇인지 런타임에 알 수 없으니 `is T` 검사를 할 방법이 없습니다. `T::class`로 클래스 정보를 얻는 것도 마찬가지입니다.

기존의 우회책은 `Class` 객체를 인자로 직접 받는 것이었습니다.

```kotlin
fun <T> isType(value: Any, clazz: Class<T>): Boolean = clazz.isInstance(value)

isType("Hello", String::class.java)
```

동작하지만 호출할 때마다 타입을 두 번 적어야 하고, 인자와 타입 매개변수가 어긋나도 컴파일러가 잡아 주지 못합니다.

## 동작 방식 {#mechanism}

`reified`는 이 문제를 **인라인을 이용해** 해결합니다.

`inline` 함수는 호출 지점에 본문이 복사됩니다. 이때 컴파일러는 그 호출이 어떤 타입으로 이루어졌는지 알고 있습니다. `isType<String>(...)`이라고 썼다면 `T`가 `String`이라는 것을 그 자리에서 알 수 있습니다.

`reified`는 그 정보를 **복사할 때 함께 박아 넣으라**는 지시입니다.

```kotlin
inline fun <reified T> isType(value: Any): Boolean = value is T

fun main() {
    val a = isType<String>("Hello")
    val b = isType<Int>("Hello")
}
```

컴파일되고 나면 `main`은 이렇게 됩니다.

```kotlin
fun main() {
    val a = "Hello" is String   // T가 String으로 치환됨
    val b = "Hello" is Int      // T가 Int로 치환됨
}
```

호출마다 `T` 자리에 실제 타입이 들어간 별개의 코드가 만들어집니다. 소거될 제네릭이 애초에 남지 않으므로 타입 소거를 피해 가는 것이 아니라 **마주칠 일 자체를 없애는** 방식입니다.

`reified`가 `inline` 함수에서만 허용되는 이유도 여기서 나옵니다. 인라인되지 않는 함수는 어디서 호출되든 쓸 수 있는 하나의 바이트코드로 컴파일되어야 하는데, 그러면 호출 시점의 타입을 박아 넣을 자리가 없습니다.

## 사용 사례 {#use-cases}

타입을 알 수 있게 되면서 그동안 막혀 있던 것들이 열립니다.

**타입 검사**

```kotlin
inline fun <reified T> isInstance(value: Any): Boolean = value is T
```

**클래스 정보 접근**

```kotlin
inline fun <reified T> printClassName() {
    println(T::class.java.name)
}

printClassName<String>()   // java.lang.String
```

**타입으로 걸러내기**

```kotlin
inline fun <reified T> List<Any>.filterByType(): List<T> = filterIsInstance<T>()

val mixed = listOf(1, "Kotlin", 2.5, "Programming")
mixed.filterByType<String>()   // [Kotlin, Programming]
```

공통점은 **`Class` 객체를 넘길 필요가 없어진다**는 것입니다. 타입을 한 번만 적으면 되고, 인자와 타입이 어긋날 여지도 사라집니다.

안드로이드에서도 이 형태를 자주 만납니다. `findFragment<MyFragment>()`처럼 타입만 적어 원하는 것을 찾아오는 API들이 대체로 `reified`로 만들어져 있습니다.

## 제약 {#limits}

- **`inline` 함수에서만 쓸 수 있습니다.** 앞에서 본 대로 인라인이 동작의 전제입니다.
- **`inline`의 대가를 함께 집니다.** 호출 지점마다 코드가 복사되므로, 자주 쓰는 함수라면 바이트코드가 늘어납니다.
- **클래스의 타입 매개변수에는 쓸 수 없습니다.** `reified`는 함수의 타입 매개변수에만 붙습니다. 클래스는 인라인되는 대상이 아니기 때문입니다.

그래서 `reified`는 아무 데나 쓰는 기능이 아니라, **타입을 다루는 작은 유틸리티 함수**에 어울립니다. 라이브러리나 프레임워크 코드에서 특히 값을 합니다.

## Pro Tips {#pro-tips}

### 바이트코드로 보는 reified {#bytecode}

`reified`는 JVM에 새로 추가된 기능이 아닙니다. 컴파일러가 코드를 만들어 내는 방식일 뿐이라는 것을 디컴파일해 보면 알 수 있습니다.

```kotlin
inline fun <reified T> isInstanceOf(value: Any): Boolean = value is T

fun main() {
    val myString: Any = "Hello, Kotlin!"

    val isString = isInstanceOf<String>(myString)
    val isInt = isInstanceOf<Int>(myString)
}
```

디컴파일하면 이렇게 나옵니다.

```java
public static final void main() {
    Object myString = "Hello, Kotlin!";

    // 호출 지점 1 — T가 String으로 대체됨
    Object value$iv = myString;
    boolean isString = value$iv instanceof String;

    // 호출 지점 2 — T가 Integer로 대체됨
    Object value$iv2 = myString;
    boolean isInt = value$iv2 instanceof Integer;
}
```

두 가지가 보입니다.

- **`isInstanceOf` 호출이 없습니다.** 본문이 `main` 안으로 복사됐기 때문입니다. `inline`이 한 일입니다.
- **`T`가 사라지고 `String`, `Integer`가 자리를 차지했습니다.** `reified`가 한 일입니다.

호출 지점마다 서로 다른 타입이 박힌 코드가 만들어졌고, 그 시점에는 제네릭이라고 부를 것이 남아 있지 않습니다. JVM 입장에서는 처음부터 `instanceof String`이라고 쓰인 평범한 코드를 실행할 뿐입니다.

`Int`가 `Integer`로 바뀐 것도 눈여겨볼 만합니다. JVM에는 원시 타입을 담는 제네릭이 없어 박싱된 타입으로 대체됩니다.

## 요약 {#summary}

> **TL;DR** — JVM은 런타임에 제네릭 타입을 지웁니다(타입 소거). `reified`는 `inline` 함수가 호출 지점에 복사될 때 `T` 자리에 실제 타입을 박아 넣게 해서, `value is T`나 `T::class`를 쓸 수 있게 합니다. 인라인이 전제이므로 `inline` 함수에서만 쓸 수 있고, 코드 복사라는 대가도 함께 집니다.

1. **타입 소거**: JVM은 컴파일 후 제네릭 타입을 제거한다. `List<String>`과 `List<Int>`가 런타임에는 둘 다 `List`.
2. **막히는 것**: 일반 제네릭 함수에서 `value is T`, `T::class`를 쓸 수 없다.
3. **`reified`가 하는 일**: 인라인으로 본문을 복사할 때 `T` 자리에 호출 시점의 실제 타입을 박아 넣는다.
4. **`inline` 전용인 이유**: 인라인되지 않으면 하나의 바이트코드로 컴파일되어 타입을 박아 넣을 자리가 없다.
5. **가능해지는 것**: 타입 검사, `T::class` 접근, `filterIsInstance`. 공통적으로 `Class` 객체를 넘기지 않아도 된다.
6. **제약**: `inline` 함수에서만, 함수의 타입 매개변수에만. 클래스에는 쓸 수 없다.
7. **어울리는 자리**: 타입을 다루는 작은 유틸리티 함수. 라이브러리와 프레임워크 코드.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 타입 소거란 무엇인가요?">

JVM이 컴파일을 마친 뒤 제네릭 타입 정보를 제거하는 것을 말합니다. 그래서 소스에서 명확히 구분되던 `List<String>`과 `List<Int>`가 런타임에는 둘 다 그냥 `List`가 됩니다. 제네릭이 없던 시절의 코드와 호환되도록 도입된 설계입니다. 이 때문에 일반 제네릭 함수 안에서는 `value is T`로 타입을 검사하거나 `T::class`로 클래스 정보를 얻을 수 없습니다. 런타임에 `T`가 무엇인지 알 방법이 없기 때문이며, 기존에는 `Class<T>` 객체를 인자로 직접 넘기는 방식으로 우회했습니다.

</def>
<def title="Q) reified는 어떻게 타입 소거 문제를 해결하나요?">

인라인을 이용합니다. `inline` 함수는 호출 지점에 본문이 복사되는데, 컴파일러는 그 호출이 어떤 타입으로 이루어졌는지 그 자리에서 알고 있습니다. `reified`는 본문을 복사할 때 타입 매개변수 자리에 그 실제 타입을 함께 박아 넣으라는 지시입니다. `isType<String>(...)`이라고 호출했다면 복사된 코드에서 `value is T`가 `value is String`이 됩니다. 결과적으로 컴파일이 끝난 코드에는 제네릭이라고 부를 것이 남지 않으므로, 타입 소거를 우회한다기보다 마주칠 일 자체를 없애는 방식에 가깝습니다.

</def>
<def title="Q) reified는 왜 inline 함수에서만 쓸 수 있나요?">

인라인이 동작의 전제이기 때문입니다. 인라인되지 않는 함수는 어디서 호출되든 사용할 수 있는 하나의 바이트코드로 컴파일되어야 하는데, 그러면 호출 시점의 타입을 박아 넣을 자리가 없습니다. 여러 호출자가 저마다 다른 타입으로 부를 텐데 코드는 하나뿐이니, 결국 타입은 소거된 상태로 남을 수밖에 없습니다. 반면 인라인되는 함수는 호출 지점마다 별개의 코드가 만들어지므로 각각에 서로 다른 실제 타입을 심을 수 있습니다. 같은 이유로 클래스의 타입 매개변수에도 `reified`를 쓸 수 없습니다. 클래스는 인라인되는 대상이 아니기 때문입니다.

</def>
<def title="Q) reified를 쓰면 무엇이 좋아지나요?">

`Class` 객체를 인자로 넘길 필요가 없어집니다. 기존에는 `isType("Hello", String::class.java)`처럼 타입을 두 번 적어야 했고 인자와 타입 매개변수가 어긋나도 컴파일러가 잡아 주지 못했지만, `reified`를 쓰면 `isType<String>("Hello")`로 한 번만 적으면 됩니다. 검사되지 않는 캐스트가 줄어 타입 안전성이 올라가고, 호출부가 짧아져 읽기도 좋아집니다. `T::class`로 클래스 메타데이터에 접근하거나 `filterIsInstance`로 타입별 필터링을 하는 것처럼 런타임 타입이 필요한 연산도 자연스럽게 표현할 수 있습니다. 안드로이드의 `findFragment<MyFragment>()` 같은 API가 이 방식으로 만들어져 있습니다.

</def>
<def title="Q) reified 함수는 바이트코드에서 어떻게 보이나요?">

호출이 사라지고 타입이 치환된 코드만 남습니다. `isInstanceOf<String>(value)`와 `isInstanceOf<Int>(value)`를 각각 호출한 코드를 디컴파일하면 `isInstanceOf` 호출 자체가 보이지 않고, 그 자리에 `value instanceof String`과 `value instanceof Integer`가 들어가 있습니다. 함수 본문이 복사된 것은 `inline`이 한 일이고, `T`가 실제 타입으로 바뀐 것은 `reified`가 한 일입니다. 이 결과를 보면 `reified`가 JVM에 새로 추가된 명령이 아니라 컴파일러가 코드를 만들어 내는 방식이라는 점이 분명해집니다. `Int`가 `Integer`로 나타나는 것은 JVM에 원시 타입을 담는 제네릭이 없어 박싱된 타입으로 대체되기 때문입니다.

</def>
</deflist>
