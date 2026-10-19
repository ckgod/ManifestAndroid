# Q29) 컬렉션 순서 정의

컬렉션의 순서를 정하는 함수는 크게 네 무리입니다. 기준에 따라 줄 세우는 `sorted` 계열, 이미 줄 서 있는지 확인하는 `isSorted` 계열, 순서를 뒤집는 `reversed`, 무작위로 섞는 `shuffled`입니다.

| 함수 | 하는 일 | 예 (`[3, 1, 2]`) |
|---|---|---|
| `sorted()` / `sortedDescending()` | 자연 순서로 오름차순 / 내림차순 정렬 | `[1, 2, 3]` / `[3, 2, 1]` |
| `sortedBy { }` / `sortedByDescending { }` | 람다가 고른 값을 기준으로 정렬 | — |
| `sortedWith(comparator)` | 직접 만든 비교 규칙으로 정렬 | — |
| `isSorted()` 등 | 정렬되어 있는지 확인 (Kotlin 2.4부터) | `false` |
| `reversed()` | 순서를 뒤집은 새 리스트 | `[2, 1, 3]` |
| `shuffled()` | 무작위로 섞은 새 리스트 | 매번 다름 |

확인만 하는 `isSorted`를 빼면 모두 원본은 바꾸지 않고 결과를 새 리스트로 돌려줍니다. 원본 자체를 바꾸는 짝은 `MutableList`에 따로 있습니다(`sort`, `reverse`, `shuffle` 등).

구현을 따라가 보면 공통된 모양이 보입니다. 기본이 되는 함수 하나(`sortedWith`)를 두고 나머지는 그 함수에 맡기며, 실제 정렬·뒤집기·섞기는 JVM에서 Java 표준 라이브러리에 넘깁니다. 아래 코드는 kotlin-stdlib 2.4.21과 JDK 25 소스 기준입니다.

## 자연 순서와 Comparator {#natural-order}

정렬하려면 "두 요소 중 어느 쪽이 앞인가"를 정할 규칙이 있어야 합니다. Kotlin에는 이 규칙을 정하는 방법이 두 가지입니다.

첫째는 요소 타입이 스스로 순서를 아는 경우입니다. `Comparable` 인터페이스를 구현한 타입은 `compareTo(other)`로 자신과 상대를 비교합니다. 결과가 음수면 내가 앞, 0이면 같음, 양수면 내가 뒤입니다. 이렇게 타입에 정해진 기본 순서를 **자연 순서**(natural order)라고 합니다. `Int`는 크기 순, `String`은 문자 코드 순입니다.

```kotlin
// NaturalOrder.kt
println(listOf("kotlin", "Android", "skydoves").sorted())   // [Android, kotlin, skydoves]
```

문자열은 사전 순이 아니라 문자 코드 순이라서, 대문자(`A` = 65)가 소문자(`k` = 107)보다 앞에 옵니다.

직접 만든 클래스도 `Comparable`을 구현하면 자연 순서를 가집니다. `sorted()`처럼 자연 순서를 쓰는 함수는 `T : Comparable<T>` 제약이 있어서, 구현하지 않은 타입에는 호출할 수 없습니다.

```kotlin
// ComparableVersion.kt
data class Version(val major: Int, val minor: Int) : Comparable<Version> {
    override fun compareTo(other: Version): Int =
        if (major != other.major) major.compareTo(other.major) else minor.compareTo(other.minor)
}

println(listOf(Version(2, 1), Version(1, 9), Version(2, 0)).sorted())
// [Version(major=1, minor=9), Version(major=2, minor=0), Version(major=2, minor=1)]
println(Version(1, 9) < Version(2, 0))   // true — <, > 연산자도 compareTo 로 바뀌어 컴파일됨
```

둘째는 비교 규칙을 요소 밖에 따로 두는 경우입니다. `Comparator`는 `compare(a, b)` 하나를 가진 객체로, 결과의 뜻은 `compareTo`와 같습니다. 같은 `Developer`라도 경력순, 이름순처럼 상황마다 다른 순서가 필요하거나, 남이 만든 클래스라 `Comparable`을 붙일 수 없을 때 씁니다. 대부분은 직접 구현하지 않고 `compareBy`, `thenBy` 같은 표준 함수로 만듭니다(아래 [sortedBy 와 sortedWith](#sorted-by)).

## sorted 와 sortedDescending {#sorted}

```kotlin
// SortedExample.kt
val names = listOf("skydoves", "kotlin", "developer")
println(names.sorted())             // [developer, kotlin, skydoves]
println(names.sortedDescending())   // [skydoves, kotlin, developer]
```

### sorted 의 두 경로 {#sorted-paths}

```kotlin
// _Collections.kt (kotlin-stdlib 2.4.21)
public fun <T : Comparable<T>> Iterable<T>.sorted(): List<T> {
    if (this is Collection) {
        if (size <= 1) return this.toList()
        @Suppress("UNCHECKED_CAST")
        return (toTypedArray<Comparable<T>>() as Array<T>).apply { sort() }.asList()
    }
    return toMutableList().apply { sort() }
}
```

크기를 아는지에 따라 길이 갈립니다.

**`Collection`인 경우** — 크기를 알 수 있습니다.

1. **0개·1개** — 정렬할 필요가 없으므로 복사만 해서 돌려줍니다.
2. **배열로 복사** — `toTypedArray()`가 크기에 딱 맞는 배열을 한 번에 만들고 요소를 옮겨 담습니다.
3. **배열 정렬** — `sort()`가 그 배열을 그 자리에서 정렬합니다. JVM에서는 `java.util.Arrays.sort()`가 호출됩니다.
4. **리스트로 감싸기** — `asList()`는 배열을 다시 복사하지 않고, 그 배열을 그대로 들여다보는 `List`를 만듭니다. JVM에서 실제 클래스는 `java.util.Arrays$ArrayList`입니다.

복사는 2단계에서 한 번만 일어납니다. 정렬 결과는 원본과 연결되지 않은 새 배열이므로, 이후 원본을 바꿔도 결과는 그대로입니다.

**그 외 `Iterable`인 경우** — 직접 만든 `Iterable` 구현처럼 크기를 미리 모릅니다. 그래서 크기에 맞는 배열을 한 번에 만들 수 없고, `toMutableList()`로 요소를 하나씩 `ArrayList`에 담은 뒤 그 리스트를 정렬합니다. `ArrayList`는 내부 배열이 차면 더 큰 배열을 만들어 옮겨 담으므로, 배열 경로보다 복사가 더 생길 수 있습니다.

`MutableList.sort()`는 JVM에서 `java.util.Collections.sort(list)` → `list.sort(null)`로 이어지고, `ArrayList`는 자기 내부 배열을 `Arrays.sort()`로 정렬합니다. 결국 두 경로 모두 같은 정렬 알고리즘에 도착하고, 차이는 그 전까지 복사를 몇 번 하느냐뿐입니다.

### JVM 에서 쓰는 정렬 알고리즘 {#sort-algorithm}

`Arrays.sort()`는 배열 종류에 따라 알고리즘이 다릅니다.

| 배열 | 알고리즘 | 같은 값끼리의 순서 |
|---|---|---|
| `int[]`, `double[]` 같은 기본 타입 배열 | 이중 피벗 퀵소트 (Dual-Pivot Quicksort) | 보장 안 함 |
| `Object[]` (객체 배열) | 팀소트 (TimSort) | 유지함 |

`sorted()`가 만드는 배열은 `Array<T>`, 즉 객체 배열입니다. `List<Int>`를 정렬해도 요소가 `Integer` 객체로 담겨 있으므로 팀소트가 쓰입니다. 책은 이중 피벗 퀵소트를 먼저 언급하지만, 그 알고리즘은 `IntArray.sort()`처럼 기본 타입 배열을 직접 정렬할 때만 쓰입니다.

팀소트는 삽입 정렬과 병합 정렬을 합친 알고리즘입니다. 데이터 안에 이미 정렬된 구간이 있으면 그 구간을 그대로 활용하므로, 실제 데이터처럼 부분적으로 정렬된 입력에서 특히 빠릅니다.

### 안정 정렬 {#stable-sort}

"같은 값끼리의 순서를 유지한다"는 성질을 **안정 정렬**(stable sort)이라고 합니다. Kotlin 문서도 `sorted` 계열은 모두 안정 정렬이라고 명시합니다.

```kotlin
// StableSort.kt
data class Developer(val name: String, val experience: Int)

val developers = listOf(
    Developer("skydoves", 5),
    Developer("kotlin", 3),
    Developer("android", 7),
    Developer("compose", 5),
)
println(developers.sortedBy { it.experience }.map { it.name })
// [kotlin, skydoves, compose, android] — 경력 5인 둘은 원래 순서(skydoves → compose)대로
```

경력이 같은 `skydoves`와 `compose`는 원래 리스트에서의 순서가 그대로 남습니다. 안정 정렬이 아니면 이 둘의 순서는 실행할 때마다 달라져도 문제가 없다는 뜻이 됩니다. 화면 목록을 다시 정렬했더니 같은 값끼리 자리가 바뀌는 일이 생기지 않는 것도 이 성질 덕분입니다.

### sortedDescending {#sorted-descending}

```kotlin
// _Collections.kt (kotlin-stdlib 2.4.21)
public fun <T : Comparable<T>> Iterable<T>.sortedDescending(): List<T> {
    return sortedWith(reverseOrder())
}
```

내림차순 정렬을 따로 구현하지 않습니다. 자연 순서를 반대로 비교하는 `Comparator`(`reverseOrder()`)를 만들어 `sortedWith`에 넘길 뿐입니다. 비교 규칙만 바꾸면 정렬 코드는 그대로 쓸 수 있다는 것이 이 계열 함수 전체에 깔린 생각입니다.

## sortedBy 와 sortedWith {#sorted-by}

`sortedBy`는 요소에서 정렬 기준이 될 값을 람다로 고릅니다. `sortedWith`는 `Comparator`를 직접 받습니다.

```kotlin
// SortedByExample.kt
println(developers.sortedBy { it.experience }.map { it.name })             // [kotlin, skydoves, compose, android]
println(developers.sortedByDescending { it.experience }.map { it.name })   // [android, skydoves, compose, kotlin]
```

### sortedWith {#sorted-with}

```kotlin
// _Collections.kt (kotlin-stdlib 2.4.21)
public fun <T> Iterable<T>.sortedWith(comparator: Comparator<in T>): List<T> {
    if (this is Collection) {
       if (size <= 1) return this.toList()
       @Suppress("UNCHECKED_CAST")
       return (toTypedArray<Any?>() as Array<T>).apply { sortWith(comparator) }.asList()
    }
    return toMutableList().apply { sortWith(comparator) }
}
```

`sorted()`와 구조가 같습니다. 다른 점은 배열을 정렬할 때 `sort()` 대신 `sortWith(comparator)`를 부른다는 것 하나입니다. JVM에서는 `Arrays.sort(array, comparator)`가 호출되고, 객체 배열이므로 역시 팀소트입니다.

`T`에 `Comparable` 제약이 없다는 점도 다릅니다. 순서는 `comparator`가 정하므로 요소 타입이 스스로 비교할 줄 몰라도 됩니다.

### sortedBy 와 compareBy {#compare-by}

```kotlin
// _Collections.kt (kotlin-stdlib 2.4.21)
public inline fun <T, R : Comparable<R>> Iterable<T>.sortedBy(crossinline selector: (T) -> R?): List<T> {
    return sortedWith(compareBy(selector))
}

public inline fun <T, R : Comparable<R>> Iterable<T>.sortedByDescending(crossinline selector: (T) -> R?): List<T> {
    return sortedWith(compareByDescending(selector))
}
```

`sortedBy`는 정렬을 직접 하지 않습니다. 람다를 `Comparator`로 바꿔서 `sortedWith`에 넘기므로, 배열 경로 같은 `sortedWith`의 최적화를 그대로 이어받습니다. 람다를 `Comparator`로 바꾸는 일은 `compareBy`가 합니다.

```kotlin
// Comparisons.kt (kotlin-stdlib 2.4.21)
public inline fun <T> compareBy(crossinline selector: (T) -> Comparable<*>?): Comparator<T> =
    Comparator { a, b -> compareValuesBy(a, b, selector) }

public inline fun <T> compareByDescending(crossinline selector: (T) -> Comparable<*>?): Comparator<T> =
    Comparator { a, b -> compareValuesBy(b, a, selector) }

public fun <T : Comparable<*>> compareValues(a: T?, b: T?): Int {
    if (a == null) return if (b == null) 0 else -1
    if (b == null) return 1

    @Suppress("UNCHECKED_CAST")
    return (a as Comparable<Any>).compareTo(b)
}
```

`compareBy`가 만든 `Comparator`는 두 요소를 받을 때마다 각각에 `selector`를 적용해 기준 값을 꺼내고, 그 값을 `compareValues`로 비교합니다. `compareValuesBy`는 이 두 단계를 묶은 함수입니다.

- **null 처리** — `compareValues`는 `null`을 어떤 값보다도 작게 취급합니다. 그래서 `sortedBy`에서 람다가 `null`을 돌려주는 요소는 맨 앞으로 갑니다.
- **내림차순** — `compareByDescending`은 비교 결과를 뒤집는 대신 **`a`와 `b`의 자리를 바꿔서** 넘깁니다. `b`를 기준으로 `a`와 비교하니 결과가 자연스럽게 반대가 됩니다. 같은 이유로 `sortedByDescending`에서는 `null`이 맨 뒤로 갑니다.

```kotlin
// SortedByNull.kt
data class User(val name: String, val nickname: String?)

val users = listOf(User("a", "zed"), User("b", null), User("c", "amy"))
println(users.sortedBy { it.nickname }.map { it.name })             // [b, c, a] — null 이 맨 앞
println(users.sortedByDescending { it.nickname }.map { it.name })   // [a, c, b] — null 이 맨 뒤
```

### 여러 기준으로 정렬 {#multiple-criteria}

첫 기준이 같을 때 쓸 두 번째 기준은 `thenBy`, `thenByDescending`으로 이어 붙입니다. 이어 붙인 결과도 `Comparator` 하나이므로 `sortedWith`에 넘깁니다.

```kotlin
// SortedWithExample.kt
val sorted = developers.sortedWith(
    compareByDescending<Developer> { it.experience }.thenBy { it.name }
)
println(sorted.map { it.name })   // [android, compose, skydoves, kotlin]
```

경력 내림차순으로 먼저 줄 세우고, 경력이 5로 같은 `skydoves`와 `compose`는 이름순으로 다시 정합니다. `thenBy`가 없었다면 둘은 안정 정렬에 따라 원래 순서인 `skydoves → compose`로 남았을 것입니다.

`compareByDescending<Developer>`처럼 타입을 적은 이유는 `thenBy`를 이어 쓰면 컴파일러가 람다의 `it` 타입을 앞에서 추론할 곳이 없기 때문입니다.

## sort 와 sorted 의 차이 {#sort-vs-sorted}

이름이 `-ed`로 끝나는 함수는 원본을 그대로 두고 새 리스트를 돌려줍니다. `-ed`가 없는 함수는 `MutableList`에만 있고, 원본을 그 자리에서 바꾼 뒤 `Unit`을 돌려줍니다.

| 새 리스트를 돌려줌 | 원본을 바꿈 (`MutableList`) |
|---|---|
| `sorted()` | `sort()` |
| `sortedDescending()` | `sortDescending()` |
| `sortedBy { }` | `sortBy { }` |
| `sortedWith(c)` | `sortWith(c)` |
| `reversed()` | `reverse()` |
| `shuffled()` | `shuffle()` |

```kotlin
// SortVsSorted.kt
val list = mutableListOf(3, 1, 2)
val copy = list.sorted()   // list 는 [3, 1, 2] 그대로, copy 는 [1, 2, 3]
list.sort()                // list 가 [1, 2, 3] 으로 바뀜. 반환값은 Unit
```

`val result = list.sort()`처럼 쓰면 `result`에는 `Unit`이 들어갑니다. 위 구현에서 보듯 `-ed` 함수는 대부분 "복사본을 만들고 그 복사본에 `-ed` 없는 함수를 호출"하는 방식으로 만들어져 있습니다.

## isSorted 계열 {#is-sorted}

Kotlin 2.4부터 정렬 여부를 확인하는 함수가 정식으로 들어왔습니다. 이름은 정렬 함수와 짝을 이룹니다. `isSorted()`, `isSortedDescending()`, `isSortedBy { }`, `isSortedByDescending { }`, `isSortedWith(comparator)`이고, `Iterable`, 배열, `Sequence`에서 모두 쓸 수 있습니다.

```kotlin
// IsSortedExample.kt
val numbers = listOf(1, 2, 3, 5, 8)
println(numbers.isSorted())             // true
println(numbers.isSortedDescending())   // false
println(listOf(1, 1, 2).isSorted())     // true — 같은 값이 이어져도 정렬된 것으로 봄
println(developers.isSortedBy { it.experience })   // false
```

```kotlin
// _Collections.kt (kotlin-stdlib 2.4.21)
@SinceKotlin("2.4")
public fun <T : Comparable<T>> Iterable<T>.isSorted(): Boolean {
    return isSortedWith(naturalOrder())
}

@SinceKotlin("2.4")
public fun <T> Iterable<T>.isSortedWith(comparator: Comparator<in T>): Boolean {
    val iterator = iterator()
    if (!iterator.hasNext()) return true
    var current = iterator.next()
    while (iterator.hasNext()) {
        val next = iterator.next()
        if (comparator.compare(current, next) > 0) return false
        current = next
    }
    return true
}
```

정렬 함수처럼 `isSorted`도 `isSortedWith` 하나에 기대고, 비교 규칙만 바꿔 넘깁니다(`naturalOrder()`, `reverseOrder()`).

`isSortedWith`는 이웃한 두 요소를 앞에서부터 차례로 비교합니다. 앞 요소가 뒤 요소보다 크다는 결과(`> 0`)가 한 번이라도 나오면 그 자리에서 `false`를 돌려주고 끝냅니다. 같은 값(`0`)은 통과시키므로 `[1, 1, 2]`도 정렬된 것으로 봅니다. 요소가 0개나 1개면 바로 `true`입니다.

이 함수가 생기기 전에는 `list == list.sorted()`로 확인하곤 했습니다. 이 방법은 확인 한 번을 위해 리스트 전체를 복사하고 O(n log n) 정렬까지 합니다. `isSorted`는 복사 없이 한 번 훑는 O(n)이고, 순서가 어긋난 곳을 만나면 나머지는 보지 않습니다. 서버나 DB에서 받은 목록이 정렬되어 왔는지 확인하거나, 정렬된 리스트에서만 올바르게 동작하는 `binarySearch`를 부르기 전에 확인할 때 적합합니다.

## reversed 와 asReversed {#reversed}

```kotlin
// ReversedExample.kt
val list = listOf("kotlin", "Android", "skydoves")
println(list.reversed())   // [skydoves, Android, kotlin]
```

`reversed()`는 정렬과 상관없이 지금 순서를 뒤집기만 합니다.

```kotlin
// _Collections.kt (kotlin-stdlib 2.4.21)
public fun <T> Iterable<T>.reversed(): List<T> {
    if (this is Collection && size <= 1) return toList()
    val list = toMutableList()
    list.reverse()
    return list
}
```

0개·1개면 뒤집어도 같으므로 복사만 합니다. 그 외에는 `toMutableList()`로 복사본을 만들고 그 복사본을 뒤집습니다. 원본은 건드리지 않습니다. `MutableList.reverse()`는 JVM에서 `java.util.Collections.reverse(list)`를 호출합니다.

### Collections.reverse 의 두 경로 {#collections-reverse}

```java
// Collections.java (JDK 25)
private static final int REVERSE_THRESHOLD = 18;

public static void reverse(List<?> list) {
    int size = list.size();
    if (size < REVERSE_THRESHOLD || list instanceof RandomAccess) {   // 경로 A
        for (int i=0, mid=size>>1, j=size-1; i<mid; i++, j--)
            swap(list, i, j);
    } else {                                                          // 경로 B
        ListIterator fwd = list.listIterator();
        ListIterator rev = list.listIterator(size);
        for (int i=0, mid=list.size()>>1; i<mid; i++) {
            Object tmp = fwd.next();
            fwd.set(rev.previous());
            rev.set(tmp);
        }
    }
}
```

Q28의 `takeLast`·`drop`과 같은 이유로 리스트 종류에 따라 길을 나눕니다.

- **경로 A (인덱스로 교환)** — `ArrayList`처럼 `RandomAccess` 표시가 붙은 리스트이거나, 18개보다 작은 리스트일 때입니다. 앞을 가리키는 `i`와 뒤를 가리키는 `j`를 두고, 두 자리의 요소를 맞바꾼 뒤 둘 다 가운데로 한 칸씩 옮깁니다. `size >> 1`은 크기를 2로 나눈 값이므로 교환은 정확히 크기의 절반만큼 일어나고, 전체는 O(n)입니다.
- **경로 B (이터레이터 두 개)** — `LinkedList`처럼 `get(index)`가 O(n)인 큰 리스트일 때입니다. 인덱스로 교환하면 매번 앞에서부터 따라가야 해서 O(n²)이 됩니다. 그래서 앞에서 출발하는 이터레이터(`fwd`)와 끝에서 출발하는 이터레이터(`rev`)를 하나씩 만들고, 각자 한 칸씩 움직이면서 현재 위치의 값을 맞바꿉니다. 이렇게 하면 O(n)을 유지합니다.

작은 리스트는 `RandomAccess`가 아니어도 경로 A를 탑니다. 요소가 몇 개 안 되면 인덱스로 따라가는 비용이 작아서, 이터레이터 두 개를 만드는 쪽이 오히려 손해이기 때문입니다.

### 배열 뒤집기 {#array-reverse}

`Array<T>`에도 `reversed()`가 있습니다. 결과는 배열이 아니라 `List`입니다.

```kotlin
// _Arrays.kt (kotlin-stdlib 2.4.21)
public fun <T> Array<out T>.reversed(): List<T> {
    if (isEmpty()) return emptyList()
    val list = toMutableList()
    list.reverse()
    return list
}
```

배열을 `ArrayList`로 복사한 뒤 `Collections.reverse()`로 뒤집으므로 `Iterable`의 `reversed()`와 같은 방식입니다. 배열 자체를 그 자리에서 뒤집는 `Array<T>.reverse()`는 Java를 거치지 않고 Kotlin 표준 라이브러리 안에 직접 구현되어 있습니다.

```kotlin
// _Arrays.kt (kotlin-stdlib 2.4.21)
public fun <T> Array<T>.reverse(): Unit {
    val midPoint = (size / 2) - 1
    if (midPoint < 0) return
    var reverseIndex = lastIndex
    for (index in 0..midPoint) {
        val tmp = this[index]
        this[index] = this[reverseIndex]
        this[reverseIndex] = tmp
        reverseIndex--
    }
}
```

1. **중간 지점** — `midPoint`는 교환할 마지막 앞쪽 인덱스입니다. 크기 5면 `5 / 2 - 1 = 1`이라 인덱스 0, 1만 교환하고, 가운데 인덱스 2는 그대로 둡니다. 크기 6이면 `6 / 2 - 1 = 2`라 인덱스 0, 1, 2를 교환합니다.
2. **0개·1개** — `midPoint`가 음수가 되므로 바로 끝냅니다.
3. **교환** — 앞쪽 `index`는 `for`문이 하나씩 늘리고, 뒤쪽 `reverseIndex`는 끝에서 시작해 직접 하나씩 줄입니다. 매번 임시 변수 `tmp`를 거쳐 두 자리의 값을 맞바꿉니다.

가운데에서 멈추는 이유는, 끝까지 돌면 이미 바꾼 쌍을 다시 바꿔서 원래대로 돌아가기 때문입니다. 원리는 `Collections.reverse`의 경로 A와 같습니다.

### asReversed {#as-reversed}

`reversed()`는 복사본을 만듭니다. 복사 없이 거꾸로 **보기만** 하고 싶으면 `asReversed()`를 씁니다. Q28의 `subList`처럼 원본을 그대로 가리키는 뷰(view)를 돌려줍니다.

```kotlin
// AsReversed.kt
val source = mutableListOf(1, 2, 3)
val copy = source.reversed()     // 복사본
val view = source.asReversed()   // 원본을 거꾸로 보는 뷰

source.add(4)
println(copy)   // [3, 2, 1]    — 만든 시점의 순서 그대로
println(view)   // [4, 3, 2, 1] — 원본 변경이 바로 보임

view[0] = 40
println(source)   // [1, 2, 3, 40] — 뷰의 0번은 원본의 마지막 자리
```

뷰는 만드는 비용이 O(1)이지만 원본과 연결되어 있다는 점을 늘 기억해야 합니다. 원본이 `MutableList`면 `asReversed()`도 `MutableList`를 돌려주므로, 뷰를 고치면 원본이 바뀝니다.

## shuffled {#shuffled}

```kotlin
// ShuffledExample.kt
val frameworks = listOf("Compose", "Flutter", "React")
println(frameworks.shuffled())   // 예: [Flutter, React, Compose] — 매번 다름
```

```kotlin
// CollectionsJVM.kt (kotlin-stdlib 2.4.21)
public actual fun <T> Iterable<T>.shuffled(): List<T> = toMutableList().apply { shuffle() }
```

복사본을 만들고 그 복사본을 섞습니다. 원본은 그대로입니다.

### Fisher-Yates 셔플 {#fisher-yates}

섞는 알고리즘은 Fisher-Yates 셔플입니다. Kotlin 표준 라이브러리에 직접 구현된 버전은 다음과 같습니다.

```kotlin
// _Collections.kt (kotlin-stdlib 2.4.21)
public fun <T> MutableList<T>.shuffle(random: Random): Unit {
    for (i in lastIndex downTo 1) {
        val j = random.nextInt(i + 1)
        this[j] = this.set(i, this[j])
    }
}
```

1. **뒤에서부터** — `i`를 마지막 인덱스에서 1까지 하나씩 줄여 갑니다.
2. **자리 뽑기** — `nextInt(i + 1)`은 0부터 `i`까지(양 끝 포함) 중 하나를 무작위로 고릅니다. 아직 자리가 정해지지 않은 앞부분에서 하나를 뽑는 것입니다. `i` 자신이 뽑힐 수도 있습니다.
3. **교환** — `i`와 `j`의 요소를 맞바꿉니다. 이렇게 `i` 자리에 들어간 요소는 확정되고, 이후 다시 움직이지 않습니다.

`this[j] = this.set(i, this[j])`는 임시 변수 없이 교환하는 한 줄입니다. `set(index, value)`는 그 자리에 새 값을 넣고 **원래 있던 값을 돌려줍니다.** 그래서 `this.set(i, this[j])`가 `j`의 값을 `i`에 넣으면서 `i`에 있던 값을 꺼내 주고, 그 값이 곧바로 `j`에 들어갑니다.

`[A, B, C, D]`로 따라가 보면 다음과 같습니다. `j`는 무작위로 이렇게 나왔다고 가정합니다.

| `i` | 뽑힌 `j` | 교환 | 결과 | 확정된 자리 |
|---|---|---|---|---|
| 3 | 1 | D ↔ B | `[A, D, C, B]` | 3번 (B) |
| 2 | 2 | C ↔ C | `[A, D, C, B]` | 2번 (C) |
| 1 | 0 | D ↔ A | `[D, A, C, B]` | 1번 (A) |

반복이 끝나면 남은 0번 자리도 저절로 확정되어 `[D, A, C, B]`가 됩니다.

각 단계에서 아직 확정되지 않은 요소 중 하나를 똑같은 확률로 뽑아 자리를 정하므로, 난수가 고르게 나온다면 n개 요소가 나올 수 있는 모든 순서(n!가지)가 같은 확률로 나옵니다. 리스트를 한 번 훑으므로 시간은 O(n)이고, 추가 공간 없이 그 자리에서 섞습니다.

`j`를 "아직 확정되지 않은 범위"(0 ~ `i`)가 아니라 전체 범위에서 뽑으면 코드는 비슷해 보여도 특정 순서가 더 자주 나오는 편향이 생깁니다. 범위를 줄여 가는 것이 이 알고리즘의 핵심입니다.

`Array<T>.shuffle(random)`도 같은 알고리즘이고, 교환만 임시 변수 `copy`를 거치는 일반적인 방식으로 씁니다.

### JVM 에서의 실제 호출 {#shuffle-jvm}

인자 없는 `shuffle()`은 위 Kotlin 코드가 아니라 Java 쪽으로 갑니다.

```kotlin
// MutableCollectionsJVM.kt (kotlin-stdlib 2.4.21)
public actual inline fun <T> MutableList<T>.shuffle() {
    java.util.Collections.shuffle(this)
}
```

따라서 JVM에서 `shuffled()`를 부르면 `Collections.shuffle()`이 섞습니다. 책은 `shuffled()`의 핵심을 `shuffle(random: Random)`으로 설명하지만, 그 Kotlin 구현은 `shuffled(Random(42))`처럼 `kotlin.random.Random`을 직접 넘길 때와 JVM이 아닌 플랫폼에서 쓰입니다.

```java
// Collections.java (JDK 25)
private static final int SHUFFLE_THRESHOLD = 5;

public static void shuffle(List<?> list, RandomGenerator rnd) {
    int size = list.size();
    if (size < SHUFFLE_THRESHOLD || list instanceof RandomAccess) {
        for (int i=size; i>1; i--)
            swap(list, i-1, rnd.nextInt(i));
    } else {
        Object[] arr = list.toArray();
        for (int i=size; i>1; i--)
            swap(arr, i-1, rnd.nextInt(i));
        ListIterator it = list.listIterator();
        for (Object e : arr) {
            it.next();
            it.set(e);
        }
    }
}
```

반복 변수가 하나 밀려 있을 뿐(`i-1`과 `nextInt(i)`) Kotlin 구현과 같은 Fisher-Yates 셔플입니다. 차이는 `reverse`처럼 리스트 종류에 따라 길을 나눈다는 점입니다. `RandomAccess`가 아닌 큰 리스트는 배열로 복사해서 섞은 뒤, 이터레이터로 하나씩 다시 써 넣습니다. 무작위 위치를 인덱스로 접근하면 O(n²)이 되기 때문입니다.

### 재현 가능한 섞기 {#reproducible-shuffle}

테스트처럼 섞은 결과가 매번 같아야 할 때는 시드(seed)를 고정한 `Random`을 넘깁니다. 시드는 난수 생성기의 시작값으로, 같은 시드면 같은 난수가 같은 순서로 나옵니다.

```kotlin
// ReproducibleShuffle.kt
val a = listOf(1, 2, 3, 4, 5).shuffled(Random(42))
val b = listOf(1, 2, 3, 4, 5).shuffled(Random(42))
println(a == b)   // true
```

## 요약 {#summary}

순서를 정하는 규칙은 타입이 스스로 가진 자연 순서(`Comparable.compareTo`)와 밖에서 넘기는 비교 규칙(`Comparator`) 두 가지입니다. `sorted`·`sortedDescending`·`sortedBy`는 모두 이 규칙을 `Comparator`로 만들어 `sortedWith`에 넘기고, `isSorted` 계열도 같은 방식으로 `isSortedWith`에 기댑니다.

`sorted`·`sortedWith`는 크기를 아는 `Collection`이면 배열로 한 번 복사해 정렬한 뒤 `asList()`로 감싸 돌려주고, 아니면 `ArrayList`에 담아 정렬합니다. JVM에서 객체 정렬은 팀소트라 안정 정렬이며, 같은 값끼리 원래 순서가 유지됩니다. `compareBy`는 `null`을 가장 작게 보고, `compareByDescending`은 두 인자의 자리를 바꿔 순서를 뒤집습니다.

`reversed`·`shuffled`는 복사본을 만든 뒤 JVM의 `Collections.reverse`·`Collections.shuffle`에 맡기고, 두 함수 모두 `RandomAccess` 여부로 인덱스 방식과 이터레이터 방식을 나눕니다. 섞기는 Fisher-Yates 알고리즘으로 O(n)에 모든 순서를 같은 확률로 만듭니다. 복사 없이 거꾸로 보려면 원본과 연결된 뷰인 `asReversed()`를 씁니다.

`-ed`로 끝나는 함수는 새 리스트를 돌려주고, `sort`·`reverse`·`shuffle`은 `MutableList` 원본을 바꾸고 `Unit`을 돌려줍니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Comparable 과 Comparator 는 각각 언제 쓰나요?">

`Comparable`은 타입 자체에 기본 순서 하나를 정할 때 씁니다. 클래스가 `compareTo`를 구현하면 그 순서가 자연 순서가 되고, `sorted()`나 `<`, `>` 연산자를 바로 쓸 수 있습니다. 버전 번호처럼 순서가 하나로 분명한 타입에 어울립니다.

`Comparator`는 비교 규칙을 타입 밖에 둡니다. 같은 `Developer`를 경력순, 이름순처럼 상황마다 다르게 정렬해야 하거나, 남이 만든 클래스라 `Comparable`을 붙일 수 없을 때 씁니다. 보통 `compareBy`, `thenBy`로 만들어 `sortedWith`에 넘깁니다.

</def>
<def title="Q) sorted() 는 왜 Collection 일 때 배열로 바꿔서 정렬하나요?">

크기를 알면 크기에 딱 맞는 배열을 한 번에 만들 수 있기 때문입니다. 요소를 배열로 한 번 복사하고, 그 배열을 `Arrays.sort()`로 그 자리에서 정렬한 뒤, `asList()`로 배열을 복사 없이 `List`로 감싸 돌려줍니다. 복사는 처음 한 번뿐입니다.

크기를 모르는 `Iterable`은 이렇게 할 수 없어서 `toMutableList()`로 `ArrayList`에 하나씩 담은 뒤 정렬합니다. 내부 배열이 찰 때마다 더 큰 배열로 옮겨 담는 복사가 더 생길 수 있습니다. 두 경로 모두 최종 정렬 알고리즘은 같습니다.

</def>
<def title="Q) 안정 정렬이란 무엇이고, Kotlin 의 sortedBy 는 안정 정렬인가요?">

정렬 기준이 같은 요소끼리는 원래 순서를 유지하는 정렬입니다. Kotlin의 `sorted` 계열은 모두 안정 정렬이라고 문서에 명시되어 있고, JVM에서는 객체 배열을 팀소트로 정렬하므로 실제로도 그렇습니다.

예를 들어 경력이 같은 두 개발자는 `sortedBy { it.experience }` 뒤에도 원래 리스트의 순서대로 남습니다. 이 순서 대신 이름순으로 정하고 싶으면 `compareBy { it.experience }.thenBy { it.name }`처럼 두 번째 기준을 붙입니다.

</def>
<def title="Q) sortedBy 에서 람다가 null 을 돌려주면 어떻게 정렬되나요?">

`sortedBy`는 `compareBy`로 만든 `Comparator`를 쓰고, 이 `Comparator`는 기준 값을 `compareValues`로 비교합니다. `compareValues`는 `null`을 어떤 값보다도 작게 취급하므로 `null`인 요소가 맨 앞에 옵니다.

`sortedByDescending`은 `compareByDescending`을 쓰는데, 이 함수는 두 인자의 자리를 바꿔서 비교합니다. 그래서 순서 전체가 뒤집히고 `null`인 요소는 맨 뒤에 옵니다.

</def>
<def title="Q) list == list.sorted() 대신 isSorted() 를 쓰면 무엇이 좋은가요?">

`list == list.sorted()`는 확인 한 번을 위해 리스트를 통째로 복사하고 O(n log n) 정렬까지 한 뒤 두 리스트를 비교합니다. Kotlin 2.4부터 들어온 `isSorted()`는 복사 없이 이웃한 두 요소를 앞에서부터 한 번씩만 비교하는 O(n)입니다.

또 순서가 어긋난 곳을 처음 만나는 순간 `false`를 돌려주고 나머지는 보지 않습니다. 받은 데이터가 기대한 순서인지 검사하거나 `binarySearch` 전에 확인하는 용도에 맞습니다.

</def>
<def title="Q) reversed() 와 asReversed() 는 무엇이 다른가요?">

`reversed()`는 원본을 `ArrayList`로 복사한 뒤 그 복사본을 뒤집어 돌려줍니다. 만든 뒤에는 원본과 아무 관계가 없습니다.

`asReversed()`는 복사하지 않고 원본을 거꾸로 들여다보는 뷰를 돌려줍니다. 만드는 비용은 O(1)이지만 원본과 연결되어 있어서, 원본에 요소를 추가하면 뷰에도 바로 보이고, 원본이 `MutableList`면 뷰를 고칠 때 원본이 바뀝니다.

</def>
</deflist>
