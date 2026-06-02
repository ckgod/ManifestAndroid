# E10) Reified Generics와 inline 함수

JVM에서 제네릭 타입 정보는 컴파일 후 사라집니다(타입 소거). 그래서 일반 함수 안에서는 `T`가 무엇인지 런타임에 알 수 없습니다. Kotlin은 `inline` 함수에 한해 `reified` 키워드로 이 한계를 우회합니다. 이 토픽은 **왜 타입 정보가 사라지는지**, **`reified`가 어떻게 그것을 되살리는지**, 그리고 그 전제 조건인 **`inline`/`noinline`/`crossinline`의 정확한 의미와 성능 영향**을 다룹니다.

## 타입 소거(Type Erasure) {#type-erasure}

### 정의 {#erasure-def}

타입 소거란 **컴파일 시점에만 존재하던 제네릭 타입 인자가, 컴파일된 바이트코드에서는 제거되는 것**입니다. JVM의 제네릭은 컴파일러가 타입을 검사하기 위한 장치일 뿐, 런타임에는 타입 인자가 남지 않습니다.

```kotlin
val a: List<String> = listOf("x")
val b: List<Int> = listOf(1)

// 런타임에는 둘 다 그냥 List다. <String>, <Int> 정보는 사라졌다.
println(a.javaClass == b.javaClass)   // true
```

`List<String>`과 `List<Int>`는 컴파일 단계에서는 다른 타입이지만, 런타임에는 동일하게 `List`(raw type)로 취급됩니다.

### 왜 소거하는가 {#why-erasure}

Java가 제네릭을 도입(Java 5)하면서 **기존 비제네릭 코드와의 하위 호환**을 지켜야 했기 때문입니다. 제네릭 이전의 `List`와 제네릭 `List<T>`가 같은 바이트코드 위에서 동작하려면, 타입 인자를 컴파일 후 지워 동일한 클래스로 수렴시키는 방식이 필요했습니다. Kotlin은 JVM 위에서 동작하므로 이 제약을 그대로 물려받습니다.

### 무엇이 막히는가 {#erasure-limits}

타입 소거 때문에, 일반 함수에서는 타입 인자 `T`를 런타임에 직접 사용할 수 없습니다.

```kotlin
fun <T> isInstanceOf(value: Any): Boolean {
    return value is T   // 컴파일 에러: Cannot check for instance of erased type: T
}
```

`value is T`, `T::class`, `T()` 같은 표현은 모두 **런타임에 `T`의 실제 타입을 알아야** 하는데, 소거 때문에 그 정보가 없어 컴파일 자체가 거부됩니다. 통상적인 우회책은 `Class<T>`를 인자로 받아 타입 정보를 명시적으로 넘기는 것입니다.

```kotlin
fun <T> fromJson(json: String, clazz: Class<T>): T = gson.fromJson(json, clazz)

// 호출할 때마다 타입을 두 번 적어야 한다
val user: User = fromJson(json, User::class.java)
```

## inline 함수 {#inline-function}

`reified`를 이해하려면 그 전제인 `inline`을 먼저 정확히 알아야 합니다.

### inline의 동작 {#inline-mechanism}

`inline` 함수는 **호출되는 자리에 함수 본문이 그대로 복사되어 들어가는** 함수입니다. 호출(call)이 사라지고, 컴파일러가 본문 코드를 호출 지점에 펼쳐 넣습니다.

```kotlin
inline fun measure(block: () -> Unit) {
    val start = System.nanoTime()
    block()
    println(System.nanoTime() - start)
}

measure { doWork() }
```

위 호출은 컴파일 후 대략 다음과 같이 펼쳐집니다.

```kotlin
val start = System.nanoTime()
doWork()                          // block()이 람다 본문으로 직접 치환됨
println(System.nanoTime() - start)
```

### 왜 inline을 쓰는가 {#why-inline}

`inline`의 본래 목적은 **고차 함수(람다를 받는 함수)의 오버헤드 제거**입니다. 람다는 보통 `Function` 객체로 컴파일되어, 호출마다 객체 생성과 가상 호출 비용이 듭니다. `inline`은 람다 본문을 호출 지점에 직접 펼쳐 이 객체 생성과 호출 비용을 없앱니다. 그래서 표준 라이브러리의 `map`, `filter`, `forEach`, `let`, `apply` 등은 모두 `inline`으로 선언되어 있습니다.

### 주의: 무분별한 inline은 손해 {#inline-caution}

`inline`은 본문을 호출 지점마다 복제하므로, **본문이 크고 호출 지점이 많으면 바이트코드 크기가 커집니다.** 따라서 `inline`은 주로 람다 파라미터를 가진 작은 함수에 적합합니다. 람다를 받지 않는 일반 함수에 `inline`을 붙이는 것은 대개 이득이 없고, 컴파일러도 경고를 냅니다.

## noinline과 crossinline {#noinline-crossinline}

`inline` 함수의 람다 파라미터는 기본적으로 모두 인라인됩니다. 이 기본 동작을 두 키워드로 제어합니다.

### noinline: 이 람다는 인라인하지 마라 {#noinline-keyword}

`inline` 함수가 람다를 여러 개 받을 때, **특정 람다만 인라인에서 제외**하고 싶을 때 씁니다. 인라인된 람다는 객체가 아니므로 변수에 담거나 다른 함수에 넘길 수 없는데, 그런 동작이 필요한 람다에 `noinline`을 붙입니다.

```kotlin
inline fun run(action: () -> Unit, noinline onError: () -> Unit) {
    try {
        action()                  // 인라인됨
    } catch (e: Exception) {
        register(onError)         // noinline이라 객체로 남아 다른 곳에 넘길 수 있다
    }
}
```

`noinline` 람다는 일반 람다처럼 `Function` 객체로 컴파일되어, 변수 저장·반환·다른 함수 전달이 가능합니다.

### crossinline: 비지역 반환을 막아라 {#crossinline-keyword}

인라인된 람다 안에서는 `return`이 **바깥 함수를 종료하는 비지역 반환(non-local return)**으로 동작합니다. 본문이 호출 지점에 펼쳐지기 때문에 가능한 일입니다.

```kotlin
inline fun forEachInt(list: List<Int>, action: (Int) -> Unit) {
    for (x in list) action(x)
}

fun find(list: List<Int>): Int? {
    forEachInt(list) {
        if (it > 10) return it     // find() 자체를 종료시킨다 (비지역 반환)
    }
    return null
}
```

그런데 람다가 **다른 실행 컨텍스트(예: 별도 스레드, 콜백)로 넘어가 호출**되면, 그 시점에는 이미 바깥 함수가 끝났을 수 있어 비지역 반환이 성립하지 않습니다. 이런 경우 컴파일러는 `crossinline`을 요구합니다. `crossinline`은 **인라인의 이점은 유지하되, 그 람다 안에서 비지역 반환을 금지**합니다.

```kotlin
inline fun runOnThread(crossinline block: () -> Unit) {
    Thread {
        block()                   // 다른 컨텍스트에서 호출됨 → 비지역 return 금지
    }.start()
}
```

이렇게 하면 `block` 안에서 바깥 함수를 끝내는 `return`은 컴파일 에러가 되고, 람다 본문 자체는 여전히 인라인됩니다.

### 세 가지 비교 {#inline-modifiers-table}

| 키워드 | 람다 인라인 여부 | 비지역 반환 | 객체로 다룰 수 있나 |
|------|------|------|------|
| (기본, inline 함수의 람다) | 인라인됨 | 허용 | 불가 |
| `noinline` | 인라인 안 됨 | 불가 | 가능(저장·전달 가능) |
| `crossinline` | 인라인됨 | 금지 | 불가 |

## reified로 타입 소거 우회 {#reified}

### reified의 동작 {#reified-mechanism}

`reified`(구체화된)는 **`inline` 함수의 타입 파라미터에만 붙일 수 있는 키워드로, 런타임에 그 타입을 실제 타입처럼 사용할 수 있게** 합니다. 핵심은 `inline`에 의존한다는 점입니다. 함수 본문이 호출 지점에 펼쳐질 때, 컴파일러가 **`T`를 호출 시점의 구체 타입으로 직접 치환**해 넣습니다. 즉 런타임에 `T`를 조회하는 것이 아니라, 컴파일 시점에 실제 타입으로 박아 넣는 것입니다.

```kotlin
inline fun <reified T> isInstanceOf(value: Any): Boolean {
    return value is T            // 정상 동작: T가 호출 지점 타입으로 치환된다
}

isInstanceOf<String>("hi")       // 컴파일 시 'value is String'으로 펼쳐진다
```

### 무엇이 가능해지는가 {#reified-capabilities}

`reified` 덕분에 일반 함수에서 막혔던 표현들이 모두 가능해집니다.

```kotlin
inline fun <reified T> demo(value: Any) {
    val check = value is T        // is 검사
    val cast = value as? T        // 캐스팅
    val klass = T::class          // KClass 획득
    val javaClass = T::class.java // java.lang.Class 획득
}
```

대표적인 실전 예시는 `Class<T>`를 받던 함수를 더 깔끔하게 바꾸는 것입니다.

```kotlin
inline fun <reified T> Gson.fromJson(json: String): T =
    fromJson(json, T::class.java)

// 타입을 한 번만 적으면 된다 — Class 인자가 사라졌다
val user: User = gson.fromJson(json)
```

안드로이드에서는 `Intent`로 액티비티를 시작할 때 자주 쓰입니다.

```kotlin
inline fun <reified T : Activity> Context.startActivity() {
    startActivity(Intent(this, T::class.java))
}

context.startActivity<DetailActivity>()
```

### reified의 제약 {#reified-limits}

`reified`는 만능이 아닙니다. 다음 제약을 정확히 알아야 합니다.

1. **반드시 `inline` 함수여야 한다.** 일반 함수나 클래스의 타입 파라미터에는 `reified`를 붙일 수 없습니다. 인라인 펼침이 타입 치환의 전제이기 때문입니다.
2. **`T()`로 인스턴스를 생성할 수 없다.** `reified`로 `T::class`는 얻을 수 있지만, `T`의 생성자가 무엇인지는 모르므로 `T()` 직접 호출은 불가합니다. 생성이 필요하면 `T::class.java.getDeclaredConstructor().newInstance()`(리플렉션) 또는 팩토리 람다를 받아야 합니다. (`Class.newInstance()`는 Java 9+에서 deprecated이므로 `getDeclaredConstructor().newInstance()`를 씁니다.)
3. **자바에서 호출할 수 없다.** `reified`는 Kotlin 컴파일러의 인라인 메커니즘에 의존하므로, 자바 코드에서는 이 함수를 호출할 수 없습니다.

## 성능 관점 {#performance}

### inline이 주는 이득 {#inline-gain}

`inline`의 성능 이득은 두 가지입니다.

1. **람다 객체 생성 제거**: 인라인되지 않은 고차 함수는 호출마다 람다를 `Function` 객체로 만듭니다. 인라인은 본문을 직접 펼쳐 이 할당을 없앱니다. 반복문 안에서 호출되는 고차 함수일수록 효과가 큽니다.
2. **가상 호출 제거**: 람다 호출은 `invoke()`에 대한 가상 호출인데, 인라인은 이를 직접 코드로 대체해 호출 비용 자체를 없앱니다.

여기에 더해, 인라인 람다는 바깥 함수의 지역 변수를 직접 참조할 수 있어 **클로저(captured variable) 박싱 비용도 줄어듭니다.**

### inline이 주는 비용 {#inline-cost}

이득만 있는 것은 아닙니다.

1. **코드 크기 증가**: 본문이 호출 지점마다 복제되므로 바이트코드가 커집니다. 본문이 크고 호출처가 많을수록 메서드 크기가 커지고, 안드로이드에서는 메서드 크기/개수가 곧 빌드와 실행 비용에 영향을 줍니다.
2. **JIT 최적화 저해 가능성**: 과도하게 큰 메서드는 JVM의 JIT 인라이닝 대상에서 제외될 수 있습니다.

그래서 실무 기준은 **람다 파라미터를 가진, 본문이 작은 함수에만 `inline`을 쓰는 것**입니다.

### reified의 성능 {#reified-performance}

`reified`는 `inline`을 강제하므로 위 인라인 비용/이득을 그대로 가집니다. 다만 `reified` 자체는 별도의 런타임 비용이 없습니다. 타입이 컴파일 시점에 박혀 들어가므로 **런타임 리플렉션이나 타입 조회가 일어나지 않습니다.** `Class<T>`를 인자로 넘기던 방식과 비교하면, `reified`는 인자 전달 한 단계를 줄이면서도 추가 런타임 비용이 없는 선택입니다.

## 요약 {#summary}

> **TL;DR** — JVM은 제네릭 타입 인자를 런타임에 지웁니다(타입 소거). 그래서 일반 함수에서는 `T is`·`T::class`가 막힙니다. Kotlin은 `inline` 함수(본문을 호출 지점에 펼치는 함수)에 한해 `reified`로 `T`를 호출 시점 타입으로 치환해 이 한계를 우회합니다. 인라인되는 람다는 `noinline`으로 인라인에서 빼거나 `crossinline`으로 비지역 반환을 금지할 수 있고, `inline`은 람다 객체·가상 호출 비용을 없애는 대신 코드 크기를 늘리므로 작은 고차 함수에만 써야 합니다.

1. **타입 소거**: JVM 하위 호환을 위해 제네릭 타입 인자는 컴파일 후 제거된다. 그래서 일반 함수에서 `value is T`, `T::class`가 불가능하다.
2. **inline 함수**: 본문을 호출 지점에 펼쳐 람다 객체 생성과 가상 호출 비용을 없앤다. `reified`의 전제 조건이다.
3. **noinline·crossinline**: `noinline`은 특정 람다를 인라인에서 제외(객체로 다룸), `crossinline`은 인라인은 유지하되 다른 컨텍스트 호출을 위해 비지역 반환을 금지한다.
4. **reified**: `inline` 함수의 타입 파라미터를 호출 시점 구체 타입으로 치환해, 타입 소거를 우회하고 런타임에 `T`를 실제 타입처럼 쓰게 한다. `inline` 필수, `T()` 생성 불가, 자바 호출 불가.
5. **성능**: inline은 할당·호출 비용을 줄이지만 코드 크기를 늘린다. reified는 추가 런타임 비용 없이 타입 정보를 확보한다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 타입 소거(type erasure)가 무엇이고, 왜 존재하나요?">

타입 소거는 컴파일 시점에만 존재하던 제네릭 타입 인자가 컴파일된 바이트코드에서 제거되는 것입니다. `List<String>`과 `List<Int>`는 컴파일 단계에서는 다른 타입이지만, 런타임에는 둘 다 그냥 `List`(raw type)로 취급되어 `javaClass`가 동일합니다.

존재하는 이유는 하위 호환입니다. Java 5에서 제네릭을 도입할 때, 제네릭 이전의 비제네릭 `List` 코드와 제네릭 `List<T>` 코드가 같은 바이트코드 위에서 함께 동작해야 했습니다. 타입 인자를 컴파일 후 지워 동일한 클래스로 수렴시키는 방식으로 이를 해결했고, JVM 위에서 동작하는 Kotlin도 이 제약을 그대로 물려받습니다. 그 결과 일반 함수에서는 `value is T`나 `T::class`처럼 런타임에 `T`의 실제 타입을 알아야 하는 코드를 쓸 수 없습니다.

</def>
<def title="Q) reified가 어떻게 타입 소거를 우회하나요? 일반 함수에는 왜 못 쓰나요?">

`reified`는 런타임에 `T`를 조회하는 것이 아니라, 컴파일 시점에 `T`를 호출 지점의 구체 타입으로 직접 치환해 넣는 방식으로 우회합니다. 예를 들어 `isInstanceOf<String>(value)`를 호출하면, 함수 본문이 호출 지점에 펼쳐지면서 `value is T`가 `value is String`으로 박혀 들어갑니다. 런타임에는 이미 실제 타입이 코드에 들어가 있으므로 소거의 영향을 받지 않습니다.

이 치환은 `inline`에 의존합니다. 함수 본문이 호출 지점에 복사·펼쳐져야 그 자리에서 타입을 박을 수 있기 때문입니다. 일반 함수는 본문이 펼쳐지지 않고 한 번만 컴파일되어 여러 타입에서 공유되므로, `T`를 특정 타입으로 박을 곳이 없습니다. 그래서 `reified`는 반드시 `inline` 함수의 타입 파라미터에만 붙일 수 있습니다.

</def>
<def title="Q) noinline과 crossinline은 각각 언제, 왜 쓰나요?">

`inline` 함수의 람다 파라미터는 기본적으로 모두 인라인되는데, 두 키워드는 이 기본 동작의 예외를 만듭니다.

`noinline`은 특정 람다를 인라인에서 제외합니다. 인라인된 람다는 객체가 아니라 펼쳐진 코드라서 변수에 담거나 다른 함수에 넘길 수 없습니다. 람다를 객체로 저장·반환·전달해야 하는 경우 그 람다에 `noinline`을 붙여 일반 `Function` 객체로 만듭니다.

`crossinline`은 인라인은 유지하되 그 람다 안에서 비지역 반환을 금지합니다. 인라인된 람다 안의 `return`은 바깥 함수를 종료하는 비지역 반환으로 동작하는데, 람다가 별도 스레드나 콜백 같은 다른 실행 컨텍스트에서 호출되면 그 시점에는 바깥 함수가 이미 끝났을 수 있어 비지역 반환이 성립하지 않습니다. 이런 경우 컴파일러가 `crossinline`을 요구하며, 람다 본문은 여전히 인라인되지만 바깥 함수를 끝내는 `return`은 컴파일 에러가 됩니다.

</def>
<def title="Q) 모든 고차 함수에 inline을 붙이면 항상 빨라지나요?">

아닙니다. `inline`은 본문을 호출 지점마다 복제하므로 트레이드오프가 있습니다. 이득은 람다가 `Function` 객체로 생성되는 할당 비용과 `invoke()` 가상 호출 비용을 없애는 것이고, 클로저 박싱 비용도 줄어듭니다. 그래서 반복문 안에서 자주 호출되는 작은 고차 함수에서 효과가 큽니다.

반면 비용은 코드 크기 증가입니다. 본문이 크고 호출처가 많으면 바이트코드가 커지고, 지나치게 커진 메서드는 JIT 인라이닝 대상에서 제외될 수도 있습니다. 그래서 실무 기준은 람다 파라미터를 가진 본문이 작은 함수에만 `inline`을 쓰는 것입니다. 람다를 받지 않는 일반 함수에 `inline`을 붙이는 것은 거의 이득이 없고, 컴파일러도 경고를 냅니다.

</def>
<def title="Q) reified 함수 안에서 T()로 인스턴스를 생성할 수 있나요?">

직접은 불가능합니다. `reified` 덕분에 `T::class`나 `T::class.java`는 얻을 수 있지만, 컴파일러가 `T`가 어떤 생성자를 가졌는지는 알지 못하므로 `T()` 호출은 컴파일되지 않습니다. 인스턴스 생성이 필요하면 `T::class.java.getDeclaredConstructor().newInstance()`처럼 리플렉션을 쓰거나(`Class.newInstance()`는 Java 9+에서 deprecated), 생성 방법을 람다로 받아 호출하는 방식을 써야 합니다.

이와 함께 기억해야 할 `reified`의 제약이 두 가지 더 있습니다. 반드시 `inline` 함수의 타입 파라미터여야 하고(일반 함수·클래스 타입 파라미터에는 불가), 인라인 메커니즘에 의존하므로 자바 코드에서는 그 함수를 호출할 수 없습니다.

</def>
</deflist>
