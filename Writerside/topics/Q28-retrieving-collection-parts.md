# Q28) 컬렉션 일부 추출

컬렉션에서 일부만 꺼내는 함수는 크게 여섯 가지입니다. 범위로 자르는 `subList`·`slice`, 앞뒤에서 개수로 자르는 `take`·`drop`, 일정 크기로 묶는 `windowed`·`chunked`입니다. 모두 원본 컬렉션은 바꾸지 않습니다.

이 함수들을 구분하는 가장 중요한 기준은 **결과가 원본을 복사한 새 리스트인가, 원본을 그대로 가리키는 뷰인가**입니다. 뷰(view)는 데이터를 따로 갖지 않고 원본의 일부를 들여다보게 해 주는 객체입니다. 여섯 가지 중 `subList`만 뷰이고, 나머지는 전부 새 리스트를 만듭니다.

| 함수 | 결과 | 받는 타입 | 예 (`[1, 2, 3, 4, 5]`) |
|---|---|---|---|
| `subList(1, 4)` | **뷰** | `List` | `[2, 3, 4]` |
| `slice(1..3)` | 새 리스트 | `List` | `[2, 3, 4]` |
| `take(2)` / `takeLast(2)` | 새 리스트 | `Iterable` / `List` | `[1, 2]` / `[4, 5]` |
| `drop(2)` / `dropLast(2)` | 새 리스트 | `Iterable` / `List` | `[3, 4, 5]` / `[1, 2, 3]` |
| `windowed(3)` | 새 리스트들의 리스트 | `Iterable` | `[[1, 2, 3], [2, 3, 4], [3, 4, 5]]` |
| `chunked(2)` | 새 리스트들의 리스트 | `Iterable` | `[[1, 2], [3, 4], [5]]` |

`subList`는 확장 함수가 아니라 `List` 인터페이스에 선언된 멤버 함수입니다. 나머지는 표준 라이브러리 `_Collections.kt`에 있는 확장 함수입니다.

## subList {#sublist}

`subList(fromIndex, toIndex)`는 `fromIndex`부터 `toIndex` 직전까지를 돌려줍니다. 끝 인덱스는 포함하지 않습니다.

```kotlin
// SubListExample.kt
val letters = listOf("A", "B", "C", "D", "E")
println(letters.subList(1, 4))   // [B, C, D]
```

### 뷰로 동작하는 방식 {#sublist-view}

Kotlin 표준 라이브러리의 `AbstractList`가 `subList`를 어떻게 구현하는지 보면 뷰가 무슨 뜻인지 알 수 있습니다.

```kotlin
// AbstractList.kt (kotlin-stdlib 2.2.21)
private class SubList<out E>(
    private val list: AbstractList<E>,   // 원본 리스트를 가리키는 참조
    private val fromIndex: Int,          // 원본에서 시작하는 위치
    toIndex: Int
) : AbstractList<E>(), RandomAccess {
    private var _size: Int = 0

    init {
        checkRangeIndexes(fromIndex, toIndex, list.size)
        this._size = toIndex - fromIndex
    }

    override fun get(index: Int): E {
        checkElementIndex(index, _size)
        return list[fromIndex + index]   // 위치를 원본 기준으로 바꿔서 원본에 물어봄
    }

    override val size: Int get() = _size

    override fun subList(fromIndex: Int, toIndex: Int): List<E> {
        checkRangeIndexes(fromIndex, toIndex, _size)
        return SubList(list, this.fromIndex + fromIndex, this.fromIndex + toIndex)
    }
}
```

`SubList`가 가진 것은 원본 참조, 시작 위치, 크기 세 가지뿐입니다. 요소를 담는 배열이 없습니다.

`get(index)`가 핵심입니다. 요청받은 위치에 `fromIndex`를 더해 원본에서의 위치로 바꾼 뒤 원본의 `get`을 호출합니다. `subList(10, 15)`로 만든 뷰에서 `get(2)`를 부르면 원본의 `get(12)`가 호출됩니다.

그래서 `subList`는 원본이 아무리 커도 **상수 시간(O(1))에** 만들어집니다. 정수 몇 개를 가진 작은 객체 하나만 만들고, 요소는 하나도 복사하지 않습니다.

`SubList`에서 다시 `subList`를 부르면 뷰 위에 뷰를 쌓지 않습니다. 시작 위치를 더해서 **원본을 직접 가리키는** 새 `SubList`를 만듭니다. 몇 번을 잘라도 `get` 한 번이 원본 `get` 한 번으로 끝납니다.

### JVM 에서의 실제 클래스 {#sublist-jvm}

위 코드는 Kotlin의 `AbstractList`를 상속한 리스트에서 쓰입니다. JVM에서 흔히 쓰는 `listOf(...)`와 `mutableListOf()`는 Java 컬렉션을 그대로 쓰기 때문에, `subList`도 Java 쪽 구현이 호출됩니다.

| 만든 방법 | 실제 클래스 (JVM) | `subList` 결과 |
|---|---|---|
| `listOf("A", "B", "C")` | `java.util.Arrays$ArrayList` | `java.util.AbstractList$RandomAccessSubList` |
| `mutableListOf(1, 2, 3)` | `java.util.ArrayList` | `java.util.ArrayList$SubList` |

클래스는 달라도 원리는 같습니다. 원본 참조와 시작 위치만 가진 뷰이고, 생성 비용은 O(1)입니다.

### 원본이 바뀌는 경우 {#sublist-mutable}

뷰는 원본과 연결되어 있으므로, 원본이 `MutableList`면 **양쪽의 변경이 서로에게 보입니다.**

```kotlin
// SubListLink.kt
val parent = mutableListOf(1, 2, 3, 4, 5)
val sub = parent.subList(1, 4)          // [2, 3, 4]

sub[0] = 99
println(parent)                         // [1, 99, 3, 4, 5] — 뷰를 고치면 원본이 바뀜

parent[2] = 77
println(sub)                            // [99, 77, 4]      — 원본을 고치면 뷰에도 보임

parent.add(6)                           // 원본의 크기가 바뀜
println(sub[0])                         // ConcurrentModificationException
```

`set`처럼 크기를 바꾸지 않는 수정은 그대로 반영됩니다. 반면 `add`·`remove`처럼 원본의 **크기를 바꾸는 수정**을 하면 뷰가 기억하는 시작 위치와 크기가 더 이상 맞지 않습니다. Java의 `ArrayList`는 이를 감지해 뷰를 쓰려는 순간 `ConcurrentModificationException`을 던집니다.

여기서 주의할 점은 **타입이 `List`라고 해서 원본이 바뀌지 않는다는 보장은 없다**는 것입니다. Kotlin의 `List`는 "이 참조로는 수정할 수 없다"는 뜻이지 내용이 영원히 그대로라는 뜻이 아닙니다.

```kotlin
// ReadOnlyIsNotImmutable.kt
val backing = mutableListOf(1, 2, 3, 4, 5)
val readOnly: List<Int> = backing       // 같은 객체를 읽기 전용 타입으로 봄
val sub = readOnly.subList(1, 3)

backing.add(6)                          // 다른 참조로 원본을 수정
println(sub)                            // ConcurrentModificationException
```

`listOf()`로 만든 리스트처럼 원본을 수정할 방법이 정말 없을 때만 뷰가 항상 안전합니다.

### 메모리 측면 {#sublist-memory}

뷰는 원본 참조를 들고 있으므로, 뷰가 살아 있는 동안 **원본 전체가 메모리에서 해제되지 않습니다.** 10만 개짜리 리스트에서 `subList(0, 10)`만 남겨 두면 요소 10개가 아니라 10만 개가 계속 메모리에 남습니다. 오래 보관할 결과라면 `subList(0, 10).toList()`나 `take(10)`으로 복사본을 만듭니다.

## slice {#slice}

`slice`는 범위나 인덱스 목록을 받아 해당 요소만 담은 **새 리스트**를 만듭니다.

```kotlin
// SliceExample.kt
val items = listOf("skydoves", "kotlin", "developer", "android")
println(items.slice(1..2))           // [kotlin, developer]
println(items.slice(listOf(3, 0)))   // [android, skydoves] — 순서도 인덱스 목록을 따름
```

받는 인자에 따라 구현이 둘로 나뉩니다.

```kotlin
// _Collections.kt (kotlin-stdlib 2.2.21)
public fun <T> List<T>.slice(indices: IntRange): List<T> {
    if (indices.isEmpty()) return listOf()
    return this.subList(indices.start, indices.endInclusive + 1).toList()
}

public fun <T> List<T>.slice(indices: Iterable<Int>): List<T> {
    val size = indices.collectionSizeOrDefault(10)
    if (size == 0) return emptyList()
    val list = ArrayList<T>(size)
    for (index in indices) {
        list.add(get(index))
    }
    return list
}
```

`IntRange` 버전은 연속된 구간이므로 `subList`로 뷰를 만든 뒤 `toList()`로 복사합니다. 요소를 하나씩 꺼내 담는 반복문을 직접 쓰지 않고, 이미 있는 두 함수를 이어 붙였습니다. `slice(1..3)`과 `subList(1, 4).toList()`는 같은 결과입니다. `IntRange`는 끝을 포함하고 `subList`는 끝을 포함하지 않으므로 `+ 1`이 붙습니다.

인덱스 목록 버전은 `listOf(3, 0, 2)`처럼 순서가 섞이거나 띄엄띄엄할 수 있어서 구간 하나로 표현할 수 없습니다. 그래서 인덱스를 하나씩 돌며 `get(index)`로 꺼내 담습니다. 결과 리스트의 용량은 인덱스 목록의 크기로 잡고, 크기를 알 수 없는 `Iterable`이면 10으로 시작합니다.

## take 와 takeLast {#take}

`take(n)`은 앞에서 n개, `takeLast(n)`은 뒤에서 n개를 담은 새 리스트를 돌려줍니다.

```kotlin
// TakeExample.kt
val names = listOf("skydoves", "kotlin", "developer")
println(names.take(2))       // [skydoves, kotlin]
println(names.takeLast(2))   // [kotlin, developer]
```

### take {#take-impl}

```kotlin
// _Collections.kt (kotlin-stdlib 2.2.21)
public fun <T> Iterable<T>.take(n: Int): List<T> {
    require(n >= 0) { "Requested element count $n is less than zero." }
    if (n == 0) return emptyList()
    if (this is Collection<T>) {
        if (n >= size) return toList()
        if (n == 1) return listOf(first())
    }
    var count = 0
    val list = ArrayList<T>(n)
    for (item in this) {
        list.add(item)
        if (++count == n)
            break
    }
    return list.optimizeReadOnlyList()
}
```

위에서부터 가장 싼 경우를 먼저 처리하는 순서입니다.

1. **음수 검사와 0개.** n이 음수면 `IllegalArgumentException`을 던집니다. 0이면 새 객체를 만들지 않고 공용 빈 리스트(`emptyList()`)를 돌려줍니다.
2. **크기를 아는 경우.** `Collection`이면 `size`를 알 수 있습니다. n이 크기 이상이면 반복문 없이 전체 복사(`toList()`)로 끝내고, n이 1이면 첫 요소 하나만 담은 리스트를 만듭니다.
3. **일반적인 경우.** 결과 리스트를 처음부터 용량 n으로 만들어 두고, 요소를 담다가 n개가 차면 바로 `break`로 빠져나옵니다. 용량을 미리 잡아 두면 `ArrayList`가 내부 배열을 늘리며 복사하는 일이 생기지 않습니다.

`Collection`이 아닌 `Iterable`은 직접 만든 `Iterable` 구현처럼 크기를 미리 알 수 없는 경우입니다. `Sequence`는 `Iterable`이 아니므로 이 함수가 아니라 `Sequence` 전용 `take`가 호출되고, 그쪽은 리스트를 만들지 않고 지연 평가되는 시퀀스를 돌려줍니다(Q27).

마지막 `optimizeReadOnlyList()`는 결과가 0개면 `emptyList()`, 1개면 `listOf(요소)`로 바꾸고, 그 외에는 그대로 돌려줍니다.

### takeLast 와 RandomAccess {#take-last}

```kotlin
// _Collections.kt (kotlin-stdlib 2.2.21)
public fun <T> List<T>.takeLast(n: Int): List<T> {
    require(n >= 0) { "Requested element count $n is less than zero." }
    if (n == 0) return emptyList()
    val size = size
    if (n >= size) return toList()
    if (n == 1) return listOf(last())
    val list = ArrayList<T>(n)
    if (this is RandomAccess) {
        for (index in size - n until size)
            list.add(this[index])
    } else {
        for (item in listIterator(size - n))
            list.add(item)
    }
    return list
}
```

앞부분은 `take`와 같은 순서입니다. 다른 점은 요소를 꺼내는 방법을 리스트 종류에 따라 고른다는 것입니다.

`RandomAccess`는 메서드가 하나도 없는 Java 인터페이스입니다. "이 리스트는 `get(index)`가 위치와 상관없이 빠르다(O(1))"는 표시로만 쓰입니다. 이렇게 타입 정보만 전달하는 인터페이스를 마커 인터페이스라고 합니다. `ArrayList`처럼 내부가 배열인 리스트가 이 표시를 붙입니다.

- **`RandomAccess`인 경우** — 인덱스로 직접 꺼냅니다. `this[index]`가 O(1)이므로 가장 빠릅니다.
- **아닌 경우** — `LinkedList` 같은 연결 리스트는 `get(index)`가 앞에서부터 따라가야 해서 O(n)입니다. 반복문 안에서 매번 `get`을 부르면 전체가 O(n²)이 됩니다. 그래서 `listIterator(size - n)`으로 시작 위치에서 이터레이터를 한 번 만들고, 거기서부터 차례로 읽습니다.

`takeLast`가 `Iterable`이 아니라 `List`에만 있는 이유도 여기서 알 수 있습니다. 뒤에서 n개를 고르려면 크기와 위치 접근이 필요한데, 일반 `Iterable`은 앞에서부터 하나씩 읽는 것밖에 못 합니다.

## drop 과 dropLast {#drop}

`drop(n)`은 앞의 n개를 뺀 나머지, `dropLast(n)`은 뒤의 n개를 뺀 나머지를 새 리스트로 돌려줍니다.

```kotlin
// DropExample.kt
val numbers = listOf(1, 2, 3, 4, 5)
println(numbers.drop(2))       // [3, 4, 5]
println(numbers.dropLast(2))   // [1, 2, 3]
```

### drop {#drop-impl}

```kotlin
// _Collections.kt (kotlin-stdlib 2.2.21)
public fun <T> Iterable<T>.drop(n: Int): List<T> {
    require(n >= 0) { "Requested element count $n is less than zero." }
    if (n == 0) return toList()
    val list: ArrayList<T>
    if (this is Collection<*>) {
        val resultSize = size - n
        if (resultSize <= 0)
            return emptyList()
        if (resultSize == 1)
            return listOf(last())
        list = ArrayList<T>(resultSize)
        if (this is List<T>) {
            if (this is RandomAccess) {           // 경로 A: 인덱스로 직접 접근
                for (index in n until size)
                    list.add(this[index])
            } else {                              // 경로 B: n 번째부터 이터레이터로 읽기
                for (item in listIterator(n))
                    list.add(item)
            }
            return list
        }
    }
    else {
        list = ArrayList<T>()
    }
    var count = 0                                 // 경로 C: 처음부터 세면서 버리기
    for (item in this) {
        if (count >= n) list.add(item) else ++count
    }
    return list.optimizeReadOnlyList()
}
```

`take`보다 길지만 구조는 같습니다. 알 수 있는 정보가 많을수록 빠른 경로를 탑니다.

- **`Collection`** — 크기를 알므로 결과 크기(`size - n`)를 계산합니다. 0 이하면 빈 리스트, 1이면 마지막 요소 하나로 바로 끝내고, 그 외에는 결과 크기만큼 용량을 잡아 둡니다.
- **`List` + `RandomAccess`** (경로 A) — 인덱스 n부터 끝까지 `this[index]`로 꺼냅니다.
- **`List`이지만 `RandomAccess`가 아님** (경로 B) — `listIterator(n)`으로 n번째 위치에서 시작하는 이터레이터를 만들어 읽습니다. `takeLast`와 같은 이유입니다.
- **그 외 `Iterable`** (경로 C) — 크기도 위치 접근도 없으므로 처음부터 하나씩 읽으며 n개를 셀 때까지는 버리고, 그 뒤부터 담습니다.

### dropLast {#drop-last}

```kotlin
// _Collections.kt (kotlin-stdlib 2.2.21)
public fun <T> List<T>.dropLast(n: Int): List<T> {
    require(n >= 0) { "Requested element count $n is less than zero." }
    return take((size - n).coerceAtLeast(0))
}
```

"뒤에서 n개 버리기"는 "앞에서 `size - n`개 가져오기"와 같습니다. 그래서 새 로직을 쓰지 않고 `take`를 그대로 재사용합니다.

`coerceAtLeast(0)`은 값이 0보다 작으면 0으로 맞추는 함수입니다. 이것이 없으면 크기보다 많이 버리려 할 때 문제가 됩니다.

- 크기 10에서 `dropLast(3)` → `take(7)` → 앞 7개
- 크기 10에서 `dropLast(12)` → `10 - 12 = -2` → `coerceAtLeast(0)`으로 0 → `take(0)` → 빈 리스트

음수가 `take`에 그대로 들어가면 `take`의 음수 검사에 걸려 예외가 납니다. 한 줄짜리 보정 덕분에 n이 크기보다 커도 예외 없이 빈 리스트가 나옵니다.

## windowed {#windowed}

`windowed(size, step)`은 크기 `size`인 창을 `step`칸씩 옮기면서, 창에 들어온 요소들을 리스트 하나로 묶어 돌려줍니다. 이런 처리를 슬라이딩 윈도우(sliding window)라고 합니다. `step`이 `size`보다 작으면 창끼리 겹칩니다.

```kotlin
// WindowedExample.kt
val numbers = listOf(1, 2, 3, 4, 5)

println(numbers.windowed(3))                                   // [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
println(numbers.windowed(3, step = 2))                         // [[1, 2, 3], [3, 4, 5]]
println(numbers.windowed(3, step = 2, partialWindows = true))  // [[1, 2, 3], [3, 4, 5], [5]]
```

`partialWindows`는 끝에서 요소가 모자라 `size`를 못 채운 창을 결과에 넣을지 정합니다. 기본값은 `false`라 버립니다.

### RandomAccess 리스트의 경로 {#windowed-random-access}

```kotlin
// _Collections.kt (kotlin-stdlib 2.2.21)
public fun <T> Iterable<T>.windowed(
    size: Int,
    step: Int = 1,
    partialWindows: Boolean = false
): List<List<T>> {
    checkWindowSizeStep(size, step)
    if (this is RandomAccess && this is List) {
        val thisSize = this.size
        val resultCapacity = thisSize / step + if (thisSize % step == 0) 0 else 1
        val result = ArrayList<List<T>>(resultCapacity)
        var index = 0
        while (index in 0 until thisSize) {
            val windowSize = size.coerceAtMost(thisSize - index)
            if (windowSize < size && !partialWindows) break
            result.add(List(windowSize) { this[it + index] })
            index += step
        }
        return result
    }
    val result = ArrayList<List<T>>()
    windowedIterator(iterator(), size, step, partialWindows, reuseBuffer = false).forEach {
        result.add(it)
    }
    return result
}
```

`ArrayList`처럼 위치 접근이 빠른 리스트는 인덱스만으로 처리합니다.

1. **결과 용량 계산** — 창 시작 위치는 0, step, 2·step, ...이므로 최대 개수는 `크기 ÷ step`을 올림한 값입니다. 이만큼 용량을 잡아 둡니다.
2. **이번 창의 크기** — `coerceAtMost`는 값이 상한을 넘으면 상한으로 맞추는 함수입니다. 남은 요소(`thisSize - index`)가 `size`보다 적으면 남은 만큼만 창에 담습니다.
3. **모자란 창 처리** — 창이 `size`보다 작고 `partialWindows`가 `false`면 거기서 끝냅니다.
4. **창 만들기** — `List(windowSize) { this[it + index] }`는 크기를 정해 두고 람다로 각 칸을 채우는 함수입니다. 원본에서 `index`부터 `windowSize`개를 복사해 새 리스트를 만듭니다.
5. **창 이동** — 시작 위치를 `step`만큼 옮깁니다.

### 그 외 Iterable 의 경로 {#windowed-iterator}

`RandomAccess`가 아니면 `windowedIterator`가 처리합니다. 위치로 접근할 수 없으므로 요소를 앞에서부터 하나씩 읽어 버퍼에 쌓고, 버퍼가 `size`만큼 차면 그 내용을 창 하나로 내보냅니다.

- `step >= size`(창이 겹치지 않음)면 일반 `ArrayList`를 버퍼로 씁니다. 창을 내보낸 뒤 비우고, 창 사이 간격(`step - size`)만큼 요소를 건너뜁니다.
- `step < size`(창이 겹침)면 원형 버퍼(`RingBuffer`)를 씁니다. 창을 내보낸 뒤 앞에서 `step`개만 지우고, 나머지는 다음 창에서 다시 씁니다. 겹치는 요소를 다시 읽지 않아도 됩니다.

### transform 을 받는 버전 {#windowed-transform}

창마다 바로 계산만 하고 창 자체는 필요 없을 때는 람다를 받는 버전을 씁니다.

```kotlin
// WindowedTransform.kt
val prices = listOf(10, 20, 30, 40, 50)
println(prices.windowed(3) { it.average() })   // [20.0, 30.0, 40.0] — 3일 이동 평균
```

이 버전은 창마다 새 리스트를 만들지 않습니다. `RandomAccess` 리스트에서는 `MovingSubList`라는 뷰 **하나**를 만들어 두고, 시작 위치만 옮겨 가며 람다에 넘깁니다. 그 외 `Iterable`에서는 버퍼 하나를 계속 재사용합니다. 창 개수만큼의 리스트 할당이 사라집니다.

대신 람다가 받은 리스트는 **람다 안에서만 유효합니다.** 공식 문서도 저장하거나 밖으로 내보내지 말라고 명시합니다. 그대로 돌려주면 모든 결과가 같은 객체를 가리키게 됩니다.

```kotlin
// WindowedEscape.kt
val windows = listOf(1, 2, 3, 4, 5).windowed(3) { it }   // 창을 그대로 반환 — 잘못된 사용
println(windows)   // [[3, 4, 5], [3, 4, 5], [3, 4, 5]] — 셋 다 같은 뷰라 마지막 위치만 보임

val ok = listOf(1, 2, 3, 4, 5).windowed(3) { it.toList() }   // 창이 필요하면 복사
println(ok)        // [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
```

## chunked {#chunked}

`chunked(size)`는 컬렉션을 `size`개씩 겹치지 않게 나눕니다. 나누어떨어지지 않으면 마지막 묶음은 남은 요소만 담습니다.

```kotlin
// ChunkedExample.kt
println(listOf(1, 2, 3, 4, 5, 6).chunked(2))   // [[1, 2], [3, 4], [5, 6]]
println(listOf(1, 2, 3, 4, 5).chunked(2))      // [[1, 2], [3, 4], [5]]
```

구현은 한 줄입니다.

```kotlin
// _Collections.kt (kotlin-stdlib 2.2.21)
public fun <T> Iterable<T>.chunked(size: Int): List<List<T>> {
    return windowed(size, size, partialWindows = true)
}
```

`chunked`는 `windowed`의 특수한 경우입니다.

- **`step = size`** — 창을 자기 크기만큼 옮기므로 창끼리 겹치지 않습니다. 첫 묶음은 0 ~ size-1, 두 번째는 size ~ 2·size-1을 담습니다.
- **`partialWindows = true`** — 끝에 남은 요소가 `size`보다 적어도 버리지 않고 마지막 묶음으로 넣습니다.

`chunked(size) { ... }`처럼 람다를 받는 버전도 `windowed`의 transform 버전에 그대로 넘기므로, 람다가 받은 리스트를 밖으로 내보내면 안 된다는 주의 사항도 같습니다. 서버에 100개씩 나눠 보내기처럼 일정 크기로 일괄 처리할 때 주로 씁니다.

## 요약 {#summary}

컬렉션 일부를 꺼내는 함수는 원본을 바꾸지 않으며, 결과가 뷰인지 복사본인지로 나뉩니다. `subList`만 원본 참조와 시작 위치만 가진 뷰라서 O(1)로 만들어지지만, 원본이 `MutableList`면 변경이 서로 보이고 원본 크기가 바뀌면 `ConcurrentModificationException`이 납니다. 원본 전체를 메모리에 붙잡아 두는 점도 주의해야 합니다.

`slice`·`take`·`drop`·`windowed`·`chunked`는 새 리스트를 만듭니다. 구현은 공통적으로 크기를 알면 용량을 미리 잡고, 0개·1개·전체 같은 경우를 먼저 처리하고, `RandomAccess` 리스트는 인덱스로, 그렇지 않은 리스트는 이터레이터로 읽어 각 상황에서 가장 빠른 방법을 고릅니다. `slice(범위)`는 `subList().toList()`, `dropLast`는 `take`, `chunked`는 `windowed`를 재사용합니다.

`windowed`·`chunked`의 transform 버전은 창마다 리스트를 만들지 않고 뷰나 버퍼 하나를 재사용하므로, 람다가 받은 리스트를 밖으로 내보내면 안 됩니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) subList 와 slice 는 결과가 같은데 무엇이 다른가요?">

`subList`는 원본을 가리키는 뷰이고 `slice`는 복사본입니다. `subList`는 요소를 복사하지 않고 원본 참조와 시작 위치만 저장하므로 원본 크기와 상관없이 O(1)로 만들어집니다. `slice(범위)`는 내부에서 `subList`로 뷰를 만든 뒤 `toList()`로 복사하므로 요소 수만큼 비용이 듭니다.

차이는 원본이 바뀔 때 드러납니다. 원본이 `MutableList`면 `subList` 결과는 원본의 변경을 그대로 보여 주고, 원본에 `add`·`remove`를 하면 이후 접근에서 `ConcurrentModificationException`이 납니다. `slice` 결과는 독립된 리스트라 영향을 받지 않습니다. 또 `subList`는 원본 전체를 메모리에 붙잡아 두므로, 큰 리스트의 일부를 오래 보관할 때는 `slice`나 `toList()`로 복사하는 편이 낫습니다.

</def>
<def title="Q) 타입이 List(읽기 전용)면 subList 는 항상 안전한가요?">

아닙니다. Kotlin의 `List`는 그 참조로 수정할 수 없다는 뜻이지 원본이 절대 바뀌지 않는다는 뜻이 아닙니다. `val readOnly: List<Int> = mutableList`처럼 같은 객체를 다른 곳에서 `MutableList`로 들고 있으면, 그쪽에서 `add`를 하는 순간 `readOnly.subList(...)`로 만든 뷰는 다음 접근에서 `ConcurrentModificationException`을 던집니다.

원본을 수정할 수 있는 참조가 어디에도 없을 때만 뷰가 항상 유효합니다.

</def>
<def title="Q) takeLast 와 drop 은 왜 RandomAccess 여부를 확인하나요?">

리스트 종류에 따라 위치 접근 비용이 다르기 때문입니다. `ArrayList`처럼 `RandomAccess` 표시가 붙은 리스트는 `get(index)`가 O(1)이라 인덱스로 직접 꺼내는 게 가장 빠릅니다.

`LinkedList` 같은 연결 리스트는 `get(index)`가 앞에서부터 따라가야 하는 O(n)이라, 반복문에서 매번 `get`을 부르면 전체가 O(n²)이 됩니다. 그래서 `listIterator(시작 위치)`로 이터레이터를 한 번만 만들고 거기서부터 차례로 읽어 O(n)을 유지합니다.

</def>
<def title="Q) dropLast 에서 coerceAtLeast(0) 은 왜 필요한가요?">

`dropLast(n)`은 `take(size - n)`으로 구현되어 있습니다. n이 크기보다 크면 `size - n`이 음수가 되고, `take`는 음수를 받으면 `IllegalArgumentException`을 던집니다. `coerceAtLeast(0)`이 음수를 0으로 맞춰 `take(0)`이 되게 하므로, 크기보다 많이 버리려 해도 예외 없이 빈 리스트가 나옵니다.

</def>
<def title="Q) windowed 와 chunked 는 어떤 관계인가요?">

`chunked(size)`는 `windowed(size, step = size, partialWindows = true)`를 호출하는 한 줄짜리 함수입니다. 창을 자기 크기만큼 옮기니 겹치지 않고, 끝에 모자란 묶음도 버리지 않습니다. `windowed`는 `step`이 `size`보다 작으면 창이 겹치고, 기본값으로는 모자란 마지막 창을 버린다는 점이 다릅니다.

둘 다 람다를 받는 버전이 있는데, 이 버전은 창마다 리스트를 만들지 않고 뷰나 버퍼 하나를 재사용합니다. 그래서 람다가 받은 리스트를 그대로 반환하거나 저장하면 모든 결과가 같은 객체를 가리키게 되므로, 필요하면 `toList()`로 복사해야 합니다.

</def>
</deflist>
