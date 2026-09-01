# Q16) inline 키워드의 장점과 한계

고차 함수는 편하지만 공짜가 아닙니다. 람다는 그 자체로 떠다니는 코드가 아니라, 함수에 넘기려면 **그 코드를 담은 객체 하나**가 되어야 합니다. 그래서 람다를 넘길 때마다 객체가 하나 만들어지고, 실행할 때는 그 객체의 `invoke()`를 한 번 거칩니다 — 코드를 곧장 실행하는 대신 한 단계 돌아가는 셈입니다.

한 번이면 티도 안 나지만, 자주 부르는 자리에서는 이 작은 비용이 쌓입니다. 그래서 나온 것이 `inline`입니다. `inline`은 **함수 본문과 넘긴 람다를 호출 지점에 그대로 펼쳐** 객체 생성도 `invoke()`도 아예 없앱니다.

```kotlin
inline fun performOperation(operation: () -> Unit) {
    println("Starting operation...")
    operation()
    println("Operation completed.")
}

fun main() {
    performOperation {
        println("Performing a task.")
    }
}
```

컴파일 결과에는 `performOperation`을 부르는 코드가 남지 않습니다. 그 자리에 함수 본문이 들어오고, 본문 안 `operation()` 자리에는 넘긴 람다의 본문이 들어옵니다.

## 동작 방식 {#mechanism}

`inline`을 붙였을 때와 붙이지 않았을 때가 어떻게 갈리는지 나란히 놓고 보겠습니다.

```kotlin
fun nonInlined(block: () -> Unit) {
    println("Before")
    block()
    println("After")
}

inline fun inlined(block: () -> Unit) {
    println("Before")
    block()
    println("After")
}

fun main() {
    nonInlined { println("A") }
    inlined { println("B") }
}
```

`main`이 컴파일된 뒤의 모습을 개념적으로 옮기면 이렇습니다.

```kotlin
fun main() {
    // nonInlined — 함수는 그대로 호출되고, 람다는 객체로 만들어져 넘어간다
    nonInlined(람다객체)

    // inlined — 함수도 람다도 사라지고 코드만 남는다
    println("Before")
    println("B")
    println("After")
}
```

위쪽은 함수 호출 한 번과 람다 객체 하나가 남고, 그 안에서 다시 `invoke()`가 호출됩니다. 아래쪽은 그 어느 것도 남지 않습니다.

## inline이 없애는 비용 {#cost-removed}

`inline` 없이 람다를 넘기면 세 가지가 따라옵니다.

1. **객체 할당** — 람다의 코드를 담을 객체가 힙에 만들어집니다.
2. **메모리 사용** — 그 객체가 살아 있는 동안 메모리를 차지하고, 결국 GC가 수거해야 합니다.
3. **가상 메서드 호출** — 람다를 실행하려면 `invoke()`를 거칩니다. 직접 호출보다 조금 느립니다.

한 번이면 무시할 만한 비용입니다. 문제는 **자주 불릴 때**입니다. 반복문 안에서 도는 함수라면 작은 객체가 계속 생기면서 비용이 쌓이고 GC에도 부담이 갑니다.

`inline`은 이 셋을 한꺼번에 없앱니다. 만들 객체가 없으니 할당도 메모리도 없고, 호출할 함수가 없으니 `invoke()`도 없습니다.

## 비지역 반환 {#non-local-return}

성능만큼 중요한 것이 `inline`이 열어 주는 문법입니다. 인라인을 썼을 때와 안 썼을 때가 어떻게 갈리는지 나란히 보겠습니다.

먼저 **인라인이 아닌** 고차 함수입니다. 여기에 넘긴 람다 안에서는 `return`으로 바깥 함수를 끝낼 수 없습니다. 시도하면 컴파일 오류입니다.

```kotlin
fun forEachPlain(list: List<Int>, action: (Int) -> Unit) {
    for (e in list) action(e)
}

fun firstEven(numbers: List<Int>): Int? {
    forEachPlain(numbers) {
        if (it % 2 == 0) return it   // 컴파일 오류: 'return' is not allowed here
    }
    return null
}
```

람다가 별도의 객체(`invoke()`를 가진)로 컴파일되기 때문입니다. 그 객체는 나중에 어디서 불릴지 알 수 없어, 그 안의 `return`이 `firstEven`까지 닿을 방법이 없습니다. 할 수 있는 건 `return@forEachPlain`으로 **람다 자신만** 빠져나오는 것뿐입니다.

이제 같은 코드에서 함수만 **인라인**으로 바꾸겠습니다.

```kotlin
inline fun forEachInline(list: List<Int>, action: (Int) -> Unit) {
    for (e in list) action(e)
}

fun firstEven(numbers: List<Int>): Int? {
    forEachInline(numbers) {
        if (it % 2 == 0) return it   // OK: firstEven() 자체를 종료한다
    }
    return null
}
```

이번엔 됩니다. 인라인되면 람다 코드가 `firstEven` 안에 그대로 펼쳐지므로, 그 `return`은 처음부터 `firstEven`에 쓰인 `return`과 다르지 않기 때문입니다. 이렇게 람다 안의 `return`이 바깥 함수를 끝내는 것을 비지역 반환(non-local return)이라고 합니다.

한 가지 짚을 것 — 비지역 반환이 끝내는 대상은 **람다를 작성한 함수**, 곧 인라인 함수를 호출한 쪽입니다. 위에서는 람다를 `firstEven` 안에서 썼으니 `firstEven`이 끝납니다. `forEachInline`이 아닙니다.

표준 라이브러리의 `forEach`가 바로 이 `inline` 형태라, `for` 루프처럼 중간에 `return`으로 빠져나올 수 있습니다. 컬렉션 함수 대부분이 `inline`인 이유이기도 합니다.

## noinline과 crossinline {#modifiers}

`inline` 함수가 받는 람다는 기본적으로 전부 인라인됩니다. 그런데 그게 곤란한 경우가 두 가지 있고, 각각에 대응하는 키워드가 있습니다.

### noinline {#noinline}

인라인된 람다는 객체가 아닙니다. 그래서 **변수에 담거나, 다른 함수에 넘기거나, 반환할 수 없습니다.** 그런 동작이 필요한 람다에는 `noinline`을 붙여 객체로 남깁니다.

```kotlin
inline fun run(action: () -> Unit, noinline onError: () -> Unit) {
    try {
        action()              // 인라인된다
    } catch (e: Exception) {
        register(onError)     // 객체로 남아 다른 곳에 넘길 수 있다
    }
}
```

람다를 여러 개 받을 때 일부만 골라 제외하는 용도입니다.

### crossinline {#crossinline}

비지역 반환은 "람다가 바깥 함수 안에서 실행된다"는 전제 위에서 성립합니다. 그런데 람다가 **다른 실행 흐름으로 넘어가서** 나중에 불린다면, 그 시점에는 바깥 함수가 이미 끝나 있을 수 있습니다. 돌아갈 곳이 없는 `return`이 되는 셈입니다.

```kotlin
inline fun runOnThread(crossinline block: () -> Unit) {
    Thread {
        block()   // 다른 스레드에서 실행된다
    }.start()
}
```

이럴 때 컴파일러가 `crossinline`을 요구합니다. **인라인은 그대로 하되, 그 람다 안에서 비지역 반환만 금지**하는 표시입니다.

### 셋의 비교 {#modifiers-comparison}

| | 인라인 | 객체로 남음 | 비지역 반환 |
|---|---|---|---|
| 기본 | O | X | 가능 |
| `noinline` | X | O | 불가 |
| `crossinline` | O | X | 불가 |

## reified 제네릭 {#reified}

`inline`이 열어 주는 것이 하나 더 있습니다. 타입 매개변수를 `reified`로 선언하면 **런타임에 그 타입을 알 수 있습니다.**

먼저 **안 되는** 쪽부터 보겠습니다. 일반 제네릭 함수에서는 `T`가 무엇인지 런타임에 알 수 없어 타입 검사를 할 수 없습니다.

```kotlin
fun <T> isInstance(value: Any): Boolean {
    return value is T      // 컴파일 오류: Cannot check for instance of erased type: T
}
```

제네릭 타입은 컴파일이 끝나면 지워지기 때문입니다(타입 소거). 런타임에는 `T`가 남아 있지 않아 `value is T`를 판단할 근거가 없습니다.

`inline` 함수로 만들고 `T`에 `reified`를 붙이면 됩니다.

```kotlin
inline fun <reified T> isInstance(value: Any): Boolean {
    return value is T      // OK
}

isInstance<String>("Hello")   // true
isInstance<Int>("Hello")      // false
```

인라인되면서 호출 지점마다 `T` 자리에 실제 타입이 박히기 때문입니다. `isInstance<String>(...)`은 `value is String`으로, `isInstance<Int>(...)`는 `value is Int`로 펼쳐집니다. 소거될 제네릭이 애초에 남지 않는 셈입니다. 그래서 `reified`는 `inline` 함수에서만 쓸 수 있습니다. 자세한 동작은 Q17에서 다룹니다.

## inline의 한계 {#limits}

이점이 분명한 만큼 대가도 분명합니다.

- **코드가 불어납니다.** 호출 지점마다 본문이 복사되므로, 함수가 크거나 호출하는 곳이 많으면 바이트코드 크기가 늘어납니다. CPU 캐시에도 불리하게 작용할 수 있습니다.
- **큰 함수에는 맞지 않습니다.** 로직이 많은 함수를 인라인하면 위 문제가 그대로 커집니다.
- **오버라이드할 수 없습니다.** 컴파일 시점에 본문이 박히므로 인라인 함수는 암묵적으로 `final`입니다. 다형성이 필요한 자리에는 쓸 수 없습니다.
- **람다를 받지 않으면 의미가 없습니다.** `inline`의 핵심 이점이 람다 객체를 없애는 것이라, 람다 파라미터가 없으면 남는 이득이 거의 없습니다. 이 경우 JVM의 JIT 컴파일러가 알아서 하는 편이 대개 낫습니다. 컴파일러도 경고로 알려 줍니다.

  ```
  warning: expected performance impact from inlining is insignificant.
  Inlining works best for functions with parameters of function types.
  ```

- **재귀 함수에는 붙일 수 없습니다.** 본문을 펼치면 그 안에 또 자기 자신이 있어 끝이 나지 않습니다. 컴파일 오류입니다.

  ```
  error: inline function 'fun fact(...)' cannot be recursive.
  ```

정리하면 **람다를 받는 작은 함수**가 `inline`의 자리입니다. 그 밖의 경우에는 붙이지 않는 편이 낫습니다.

## Pro Tips {#pro-tips}

### 인라인 프로퍼티 {#inline-property}

`inline`은 함수뿐 아니라 프로퍼티의 접근자에도 붙일 수 있습니다. getter나 setter 코드가 호출 지점에 그대로 들어가 메서드 호출 비용이 사라집니다.

```kotlin
inline val isUserActive: Boolean
    get() = System.currentTimeMillis() - lastActivityTime < ACTIVE_THRESHOLD
```

조건이 하나 있습니다. **backing field가 있는 프로퍼티에는 붙일 수 없습니다.** 인라인은 접근자의 코드를 호출부로 옮기는 일인데, 저장소를 읽는 코드는 그렇게 옮길 수가 없기 때문입니다.

Q10에서 본 기준이 그대로 적용됩니다. 커스텀 getter만 있고 `field`를 참조하지 않는 프로퍼티라면 backing field가 생기지 않으므로 `inline`을 붙일 수 있고, 값을 저장하는 프로퍼티라면 붙일 수 없습니다.

### repeat과 map이 suspend 람다를 받는 이유 {#suspend-inline}

`repeat`은 `suspend` 함수가 아닙니다. 그런데 아래 코드가 동작합니다.

```kotlin
suspend fun printMessage(message: String) {
    println("Message: $message")
}

suspend fun main() {
    repeat(3) {
        printMessage("skydoves $it")   // suspend 함수를 호출하고 있다
    }
}
```

`repeat`이 `inline`이기 때문입니다. 인라인되고 나면 이 코드는 사실상 아래와 같아집니다.

```kotlin
suspend fun main() {
    for (i in 0 until 3) {
        printMessage("skydoves $i")
    }
}
```

`repeat` 호출이 사라지고 람다 본문이 `main` 안에 그대로 놓입니다. 그러면 `printMessage`는 `suspend fun main` 안에서 직접 호출되는 것이 되므로 아무 문제가 없습니다.

인라인이 아니었다면 람다는 별도의 함수 객체가 되고, 그 객체의 `invoke()`는 `suspend`가 아니므로 안에서 `suspend` 함수를 부를 수 없습니다. `map`, `filter`, `forEach`가 코루틴을 전혀 모르는 시그니처를 가지고도 `suspend` 람다와 함께 쓰이는 것이 같은 이유입니다.

## 요약 {#summary}

> **TL;DR** — `inline`은 함수 본문과 넘긴 람다를 호출 지점에 펼쳐 람다 객체 생성과 `invoke()` 호출을 없앱니다. 덤으로 비지역 반환과 `reified`가 가능해집니다. 대가는 호출부마다 코드가 복사된다는 것이고, 그래서 **람다를 받는 작은 함수**에만 어울립니다.

1. **하는 일**: 함수 본문과 람다를 호출 지점에 복사한다. 호출도 객체도 남지 않는다.
2. **없애는 비용**: 람다 객체 할당, 그 메모리, `invoke()` 가상 호출. 반복 호출될수록 이득이 커진다.
3. **비지역 반환**: 인라인된 람다 안의 `return`은 바깥 함수를 종료한다. 컬렉션 함수가 언어 구문처럼 읽히는 이유.
4. **`noinline`**: 그 람다만 객체로 남긴다. 변수에 담거나 다른 함수에 넘겨야 할 때.
5. **`crossinline`**: 인라인은 유지하되 비지역 반환만 막는다. 람다가 다른 실행 흐름에서 불릴 때.
6. **`reified`**: 인라인 덕분에 런타임에 타입을 알 수 있다 (Q17).
7. **한계**: 코드 크기 증가, 오버라이드 불가, 재귀 불가, 람다가 없으면 효과 없음.
8. **기준**: 람다를 받는 작은 함수에만 붙인다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) inline 키워드는 무엇을 하나요?">

컴파일러에게 함수를 호출하지 말고 그 본문을 호출 지점에 그대로 펼치라고 지시합니다. 함수에 넘긴 람다도 함께 펼쳐집니다. 그 결과 람다를 담을 객체가 만들어지지 않고, 함수 호출과 람다의 `invoke()` 호출도 사라집니다. 한 번의 호출이라면 무시할 만한 차이지만, 반복문 안처럼 자주 불리는 자리에서는 작은 객체가 계속 생기면서 비용이 누적되고 GC에도 부담이 가므로 효과가 분명해집니다. 표준 라이브러리의 컬렉션 함수 대부분이 `inline`으로 선언되어 있는 것이 이 때문입니다.

</def>
<def title="Q) 비지역 반환이란 무엇이며 왜 inline에서만 가능한가요?">

람다 안에서 쓴 `return`이 람다가 아니라 그 람다를 감싸는 바깥 함수를 종료하는 것을 말합니다. 일반 람다는 별도의 함수 객체로 컴파일되므로 그 안의 `return`이 바깥 함수까지 닿을 수 없고, `return@label`로 람다 자신만 빠져나올 수 있습니다. 반면 인라인된 람다는 코드가 바깥 함수 안에 그대로 복사되기 때문에, 그 `return`은 처음부터 바깥 함수에 쓰인 `return`과 다르지 않습니다. 덕분에 인라인 함수가 `for`나 `while` 같은 언어 내장 구문처럼 자연스럽게 동작합니다.

</def>
<def title="Q) noinline과 crossinline은 각각 언제 쓰나요?">

`noinline`은 인라인에서 제외하고 싶은 람다에 붙입니다. 인라인된 람다는 객체가 아니라서 변수에 담거나 다른 함수에 넘기거나 반환할 수 없는데, 그런 처리가 필요한 람다에 붙이면 일반 람다처럼 객체로 남습니다. `crossinline`은 인라인은 그대로 두되 비지역 반환만 금지합니다. 람다가 별도의 스레드나 콜백처럼 다른 실행 흐름으로 넘어가 나중에 실행되면 그 시점에는 바깥 함수가 이미 끝나 있을 수 있어 비지역 반환이 성립하지 않는데, 이런 경우 컴파일러가 `crossinline`을 요구합니다.

</def>
<def title="Q) inline을 붙이면 안 되는 경우는 언제인가요?">

첫째로 함수가 클 때입니다. 호출 지점마다 본문이 복사되므로 호출하는 곳이 많으면 바이트코드가 크게 불어납니다. 둘째로 람다 파라미터가 없을 때입니다. `inline`의 핵심 이점이 람다 객체를 없애는 것이라 람다가 없으면 남는 이득이 거의 없고, 이 경우 JVM의 JIT 컴파일러에 맡기는 편이 대개 낫습니다. 컴파일러도 "expected performance impact from inlining is insignificant"라는 경고를 냅니다. 그 밖에 오버라이드가 필요한 함수는 인라인 함수가 암묵적으로 `final`이라 쓸 수 없고, 재귀 함수는 본문을 펼치는 일이 끝나지 않으므로 컴파일 오류가 납니다.

</def>
<def title="Q) inline 프로퍼티는 무엇이고 어떤 제약이 있나요?">

getter나 setter에 `inline`을 붙여 접근자의 코드를 호출 지점에 직접 펼치는 프로퍼티입니다. 프로퍼티에 자주 접근하면서 접근자가 가벼운 연산만 할 때 메서드 호출 비용을 없앨 수 있습니다. 제약은 backing field가 있는 프로퍼티에는 붙일 수 없다는 것입니다. 인라인은 접근자의 코드를 호출부로 옮기는 일인데 저장소를 직접 읽는 코드는 그렇게 옮길 수 없기 때문입니다. Q10에서 본 기준이 그대로 적용되어, 커스텀 getter만 있고 `field`를 참조하지 않는 프로퍼티라면 backing field가 없으므로 붙일 수 있습니다.

</def>
<def title="Q) repeat이나 map은 suspend 함수가 아닌데 어떻게 람다에서 suspend 함수를 호출할 수 있나요?">

이 함수들이 `inline`으로 선언되어 있기 때문입니다. 인라인되면 함수 호출이 사라지고 람다 본문이 호출한 쪽의 코드 안에 그대로 놓입니다. 호출한 곳이 `suspend` 함수라면 람다 본문도 그 `suspend` 함수 안에 있는 코드가 되므로, 그 안에서 다른 `suspend` 함수를 부르는 데 아무 문제가 없습니다. 인라인이 아니었다면 람다는 별도의 함수 객체가 되고 그 객체의 `invoke()`는 `suspend`가 아니므로 안에서 `suspend` 함수를 호출할 수 없습니다. `map`, `filter`, `forEach`가 코루틴을 모르는 시그니처를 가지고도 `suspend` 람다와 함께 쓰이는 것이 같은 이유입니다.

</def>
</deflist>
