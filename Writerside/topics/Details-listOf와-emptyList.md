# Details: listOf() 와 emptyList()

`listOf()`와 `emptyList()`는 둘 다 읽기 전용 리스트를 만듭니다. 그리고 인자 없이 쓴 `listOf()`는 내부적으로 `emptyList()`와 **같은 결과**를 돌려줍니다. 차이는 성능이 아니라 의도의 표현에 있습니다.

## listOf() 의 동작 {#list-of}

`listOf()`는 읽기 전용 리스트를 만드는 범용 함수입니다. 가변 개수의 인자를 받아 그 요소들을 담은 리스트를 만듭니다.

```kotlin
// ListOfExample.kt
val nonEmptyList = listOf("skydoves", "kotlin", "developer")
println(nonEmptyList)       // [skydoves, kotlin, developer]

val emptyUsingListOf = listOf<String>()
println(emptyUsingListOf)   // []
```

구현을 보면 인자가 하나라도 있는지 먼저 확인하고, 없으면 `emptyList()`에 그대로 넘깁니다.

```kotlin
// ListOfImplementation.kt
public fun <T> listOf(vararg elements: T): List<T> =
    if (elements.size > 0) elements.asList() else emptyList()
```

즉 인자 없는 `listOf()`는 실질적으로 `emptyList()`입니다.

## emptyList() 의 동작 {#empty-list}

`emptyList()`는 빈 리스트 전용 함수입니다. 인자를 받지 않고, **항상 같은 싱글턴 인스턴스**를 돌려줍니다.

```kotlin
// emptyList().kt
public fun <T> emptyList(): List<T> = EmptyList
```

`EmptyList`는 `internal object`로 선언된 싱글턴입니다.

```kotlin
// EmptyList.kt
internal object EmptyList : List<Nothing>, Serializable, RandomAccess {
    override val size: Int get() = 0
    override fun isEmpty(): Boolean = true
    override fun contains(element: Nothing): Boolean = false

    override fun get(index: Int): Nothing =
        throw IndexOutOfBoundsException("Empty list doesn't contain element at index $index.")
    // ... 나머지 오버라이드
}
```

`size`는 항상 0, `isEmpty()`는 항상 `true`, `get(index)`는 항상 예외를 던지도록 하드코딩되어 있습니다. 빈 리스트로만 동작하도록 못 박은 구현입니다.

## 싱글턴 확인 {#singleton}

실제로 같은 인스턴스가 돌아오는지 확인해 보면 이렇습니다.

```kotlin
val a = listOf<String>()
val b = emptyList<String>()
val c = listOf<Int>()

println(a::class.java.name)   // kotlin.collections.EmptyList
println(b::class.java.name)   // kotlin.collections.EmptyList
println(a === b)              // true
println(a === c)              // true
```

주목할 것은 마지막 줄입니다. `List<String>`과 `List<Int>`인데도 같은 인스턴스입니다.

이것이 가능한 이유는 `EmptyList`가 `List<Nothing>`을 구현하기 때문입니다. `Nothing`은 모든 타입의 하위 타입이므로 `List<Nothing>`은 모든 `List<T>`의 하위 타입이 됩니다. 원소가 하나도 없으니 원소 타입이 무엇이든 안전하게 통용됩니다. 애플리케이션 전체에서 빈 리스트는 객체 하나로 충분합니다.

접근을 시도하면 미리 준비된 메시지가 나옵니다.

```
IndexOutOfBoundsException: Empty list doesn't contain element at index 0.
```

## 선택 기준 {#choosing}

성능은 같습니다. 어느 쪽을 쓰든 같은 싱글턴이 돌아오므로 메모리나 속도에서 차이가 없습니다.

갈리는 것은 읽는 사람에게 전달되는 의도입니다.

| 상황 | 권장 |
|---|---|
| 빈 리스트를 만들려는 의도가 분명할 때 | `emptyList()` |
| 요소를 나열해 리스트를 만들 때 | `listOf(a, b, c)` |
| 기본값·초기값·조기 반환 | `emptyList()` |

`emptyList()`는 이름 자체가 "여기는 비어 있다"를 말해 줍니다. `listOf<String>()`은 한 번 더 읽어야 빈 리스트임을 알 수 있습니다. 코틀린에서는 `emptyList()` 쪽이 권장되는 표현입니다.

`emptySet()`, `emptyMap()`도 같은 구조로 되어 있습니다.

## 요약 {#summary}

`listOf()`는 요소가 있든 없든 리스트를 만드는 범용 함수이고, 인자가 없으면 `emptyList()`에 위임합니다. `emptyList()`는 빈 리스트 전용 함수로, 호출할 때마다 새 객체를 만들지 않고 `EmptyList` 싱글턴을 돌려줍니다.

`EmptyList`가 `List<Nothing>`을 구현하는 덕분에 원소 타입과 무관하게 같은 인스턴스를 재사용할 수 있습니다. 결과와 성능이 동일하므로 선택 기준은 의도의 명확성이며, 빈 리스트를 뜻할 때는 `emptyList()`가 더 읽기 좋습니다.
