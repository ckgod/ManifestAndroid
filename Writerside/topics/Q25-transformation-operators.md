# Q25) 변환 연산자

변환 연산자는 원본 컬렉션을 건드리지 않고 **새 컬렉션을 만들어 돌려주는** 함수들입니다. `map`, `flatMap`, `groupBy`, `zip`, `filter`가 대표적입니다.

이들은 공통된 구조를 갖고 있습니다. 겉으로 보이는 함수는 얇은 래퍼이고, 실제 일은 `~To` 로 끝나는 헬퍼가 합니다. 이 구조를 한 번 보면 나머지는 전부 같은 방식으로 읽힙니다.

## map 과 mapIndexed {#map}

`map`은 각 요소에 함수를 적용해 변환된 요소들의 새 컬렉션을 돌려줍니다. 인덱스가 같이 필요하면 `mapIndexed`를 씁니다.

```kotlin
// Map Example.kt
val names = listOf("skydoves", "kotlin", "developer")
val uppercased = names.map { it.uppercase() }
println(uppercased)   // [SKYDOVES, KOTLIN, DEVELOPER]
```

내부를 보면 `map` 자체에는 변환 로직이 없습니다.

```kotlin
// Map Internals.kt
public inline fun <T, R> Iterable<T>.map(transform: (T) -> R): List<R> {
    return mapTo(ArrayList<R>(collectionSizeOrDefault(10)), transform)
}

internal fun <T> Iterable<T>.collectionSizeOrDefault(default: Int): Int =
    if (this is Collection<*>) this.size else default

public inline fun <T, R, C : MutableCollection<in R>> Iterable<T>.mapTo(
    destination: C, transform: (T) -> R
): C {
    for (item in this)
        destination.add(transform(item))
    return destination
}
```

두 단계로 나뉩니다.

첫째, **결과를 담을 리스트를 미리 만듭니다.** 이때 `collectionSizeOrDefault(10)`으로 크기를 가늠합니다. 수신 객체가 `Collection`이면 `size`를 알 수 있으므로 그 크기로 `ArrayList`를 만들고, `Sequence`처럼 크기를 모르면 기본값 10을 씁니다. 크기를 미리 맞춰 두면 요소를 넣는 동안 내부 배열을 여러 번 늘리지 않아도 됩니다.

둘째, **`mapTo`에 위임합니다.** 실제 반복과 변환은 여기서 일어납니다.

## flatMap 과 flatten {#flatmap}

`flatMap`은 각 요소를 컬렉션으로 바꾼 뒤 그 결과를 한 겹 펼쳐 하나의 리스트로 만듭니다.

```kotlin
// FlatMap Example.kt
val nestedLists = listOf(
    listOf("kotlin", "android"),
    listOf("developer", "tools")
)
println(nestedLists.map { it })       // [[kotlin, android], [developer, tools]]
println(nestedLists.flatMap { it })   // [kotlin, android, developer, tools]
```

구조는 `map`과 같지만 초기 용량 계산이 빠져 있습니다.

```kotlin
// FlatMap Internals.kt
public inline fun <T, R> Iterable<T>.flatMap(transform: (T) -> Iterable<R>): List<R> {
    return flatMapTo(ArrayList<R>(), transform)
}

public inline fun <T, R, C : MutableCollection<in R>> Iterable<T>.flatMapTo(
    destination: C, transform: (T) -> Iterable<R>
): C {
    for (element in this) {
        val list = transform(element)
        destination.addAll(list)
    }
    return destination
}
```

`transform`이 길이를 알 수 없는 컬렉션을 돌려주므로 최종 크기를 미리 계산할 수 없기 때문입니다. 그래서 기본 크기의 `ArrayList`로 시작합니다.

이미 중첩된 컬렉션을 펼치기만 할 때는 `flatten()`을 쓰면 됩니다.

## groupBy 와 associateBy {#group-associate}

리스트를 맵으로 재구성할 때 씁니다. **`groupBy`는 키마다 요소를 모두 보존하고**(값이 리스트), **`associateBy`는 키마다 하나만 남깁니다**(충돌하면 마지막 것).

```kotlin
// GroupBy Example.kt
val developers = listOf("Alice", "Bob", "Ben", "Charlie")
println(developers.groupBy { it.length })   // {5=[Alice], 3=[Bob, Ben], 7=[Charlie]}
```

집계가 목적이면 `groupBy`, 고유한 키로 빠르게 찾는 것이 목적이면 `associateBy`가 맞습니다.

```kotlin
// GroupBy Internals.kt
public inline fun <T, K> Iterable<T>.groupBy(keySelector: (T) -> K): Map<K, List<T>> {
    return groupByTo(LinkedHashMap<K, MutableList<T>>(), keySelector)
}

public inline fun <T, K, M : MutableMap<in K, MutableList<T>>> Iterable<T>.groupByTo(
    destination: M, keySelector: (T) -> K
): M {
    for (element in this) {
        val key = keySelector(element)
        val list = destination.getOrPut(key) { ArrayList<T>() }
        list.add(element)
    }
    return destination
}
```

여기서 `LinkedHashMap`을 고른 것은 의도적입니다. 키의 삽입 순서가 보존되므로, 결과 맵의 키는 **원본에서 그 키가 처음 등장한 순서**대로 나옵니다. 매번 같은 입력에 같은 순서가 보장됩니다.

각 키의 리스트는 `getOrPut`으로 가져오거나 없으면 만듭니다.

## zip 과 unzip {#zip}

`zip`은 두 컬렉션을 위치별로 짝지어 `Pair`의 리스트를 만듭니다. `unzip`은 그 역연산입니다.

```kotlin
// Zip Example.kt
val languages = listOf("Kotlin", "Java")
val versions = listOf("1.8", "11")
println(languages.zip(versions))   // [(Kotlin, 1.8), (Java, 11)]
```

`zip`은 오버로드가 둘입니다. 간단한 쪽은 범용적인 쪽에 위임합니다.

```kotlin
// Zip Internals.kt
public infix fun <T, R> Iterable<T>.zip(other: Iterable<R>): List<Pair<T, R>> {
    return zip(other) { t1, t2 -> t1 to t2 }
}

public inline fun <T, R, V> Iterable<T>.zip(
    other: Iterable<R>, transform: (a: T, b: R) -> V
): List<V> {
    val first = iterator()
    val second = other.iterator()
    val list = ArrayList<V>(
        minOf(collectionSizeOrDefault(10), other.collectionSizeOrDefault(10))
    )
    while (first.hasNext() && second.hasNext()) {
        list.add(transform(first.next(), second.next()))
    }
    return list
}
```

세 가지를 볼 만합니다.

`iterator()`를 직접 꺼내 쓰므로 `List`든 `Set`이든 `Sequence`든 같은 방식으로 처리됩니다.

초기 용량을 **두 컬렉션 크기의 최솟값**으로 잡습니다. 어느 한쪽이 먼저 소진되면 거기서 멈추기 때문입니다.

그 규칙은 `while` 조건에 그대로 드러납니다. `first.hasNext() && second.hasNext()` 이므로 **짧은 쪽 길이에 맞춰 잘립니다.** 길이가 다른 두 리스트를 `zip`하면 남는 쪽은 버려집니다.

## filter 계열 {#filter}

조건으로 요소를 고르거나 걸러 냅니다.

```kotlin
// Filter Example.kt
val items = listOf("skydoves", "kotlin", "android")
println(items.filter { it.startsWith("k") })   // [kotlin]
```

`filter`는 조건에 맞는 것을 남기고, `filterNot`은 제외하며, `filterIndexed`는 인덱스도 함께 봅니다. 부정 조건은 `!condition`보다 `filterNot`이 읽기 좋습니다.

```kotlin
// Filter Internals.kt
public inline fun <T> Iterable<T>.filter(predicate: (T) -> Boolean): List<T> {
    return filterTo(ArrayList<T>(), predicate)
}

public inline fun <T, C : MutableCollection<in T>> Iterable<T>.filterTo(
    destination: C, predicate: (T) -> Boolean
): C {
    for (element in this)
        if (predicate(element))
            destination.add(element)
    return destination
}
```

`map`과 달리 초기 용량을 계산하지 않습니다. 몇 개가 조건을 통과할지 미리 알 수 없기 때문입니다.

## inline 의 역할 {#inline}

이 연산자들은 대부분 `inline` 함수입니다. 우연이 아니라 성능을 위한 선택입니다.

인라인이 아니라면 `filter { ... }`를 부를 때마다 람다를 담을 `Function` 객체가 생깁니다. 인라인이면 컴파일러가 `filterTo`의 루프와 람다 본문을 **호출한 자리에 그대로 복사**합니다. 결과적으로 손으로 쓴 `for` + `if` 와 거의 같은 바이트코드가 됩니다. 선언적으로 쓰면서 성능을 잃지 않는 이유입니다.

부수 효과도 큽니다. 람다 본문이 호출 지점에 복사되므로 **바깥 문맥을 그대로 물려받습니다.** 그래서 `map { }` 안에서 `suspend` 함수를 부를 수 있고, `@Composable` 함수 안의 `forEach { }` 안에서 다른 `@Composable`을 부를 수 있습니다. 인라인이 아닌 람다에서는 둘 다 금지된 동작입니다.

자세한 것은 Q16에서 다뤘습니다.

## 반환 타입과 중간 리스트 {#intermediate}

두 가지를 알아 둘 필요가 있습니다.

첫째, **반환 타입은 언제나 `List`입니다.** 수신 객체가 `Set`이든 `Map`이든 마찬가지입니다.

```kotlin
val s: Set<Int> = setOf(1, 2, 3)
val mapped = s.map { it * 2 }
println(mapped::class.java.name)   // java.util.ArrayList
```

`Set`에 `map`을 걸면 중복이 다시 생길 수 있습니다. 집합을 유지하려면 `toSet()`을 붙여야 합니다.

둘째, **연산자를 이을 때마다 중간 리스트가 새로 생깁니다.** 각 단계가 독립적으로 `ArrayList`를 만들어 채우고 돌려주기 때문입니다.

```kotlin
val result = (1..5)
    .map { it * 2 }      // 리스트 1개 생성
    .filter { it > 4 }   // 리스트 1개 더 생성
    .map { it + 1 }      // 리스트 1개 더 생성
```

원소가 적으면 문제가 안 됩니다. 그러나 컬렉션이 커지면 이 비용이 드러납니다.

```kotlin
var calls = 0
val first = (1..1000).map { calls++; it * 2 }.first()
println("$first, map 람다 호출 $calls 회")   // 2, map 람다 호출 1000 회
```

첫 원소 하나만 필요한데 1,000번을 전부 계산했습니다. `map`이 리스트를 완성한 뒤에야 `first()`가 실행되기 때문입니다.

같은 코드에 `asSequence()`만 넣으면 달라집니다.

```kotlin
var calls = 0
val first = (1..1000).asSequence().map { calls++; it * 2 }.first()
println("$first, map 람다 호출 $calls 회")   // 2, map 람다 호출 1 회
```

1,000번이 1번이 됐습니다. `Sequence`는 중간 리스트를 만들지 않고 원소 하나씩 끝까지 흘려보내며, 필요한 만큼만 계산합니다. 이 차이는 Q27에서 자세히 다룹니다.

## 요약 {#summary}

`map`, `flatMap`, `groupBy`, `zip`, `filter`는 모두 같은 구조입니다. 겉의 함수는 결과를 담을 컬렉션을 준비하는 얇은 래퍼이고, 실제 반복과 변환은 `mapTo`·`flatMapTo`·`groupByTo`·`filterTo` 같은 헬퍼가 맡습니다. 크기를 미리 알 수 있는 `map`과 `zip`은 초기 용량까지 맞춰 잡습니다.

대부분 `inline` 함수라 람다 객체가 생기지 않고, 그 덕에 내부에서 `suspend`나 `@Composable` 함수를 부를 수 있습니다.

반환 타입은 항상 `List`이고, 연산자를 이을 때마다 중간 리스트가 새로 생깁니다. 컬렉션이 크거나 앞쪽 결과만 필요한 경우에는 `asSequence()`로 바꾸는 것이 훨씬 유리합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) map 은 내부적으로 어떻게 동작하나요?">

`map`은 두 단계로 나뉩니다. 먼저 결과를 담을 `ArrayList`를 만드는데, 이때 `collectionSizeOrDefault(10)`으로 초기 용량을 정합니다. 수신 객체가 `Collection`이면 `size`를 알 수 있으므로 그 크기로 만들고, `Sequence`처럼 크기를 모르면 기본값 10을 씁니다. 크기를 맞춰 두면 요소를 넣는 동안 내부 배열을 반복해서 늘리지 않아도 됩니다.

그다음 `mapTo`에 그 리스트와 람다를 넘깁니다. 실제 반복과 변환은 여기서 일어납니다. 즉 `map` 자체에는 변환 로직이 없고, 준비만 한 뒤 범용 헬퍼에 위임하는 구조입니다. `filter`, `flatMap`, `groupBy`도 모두 같은 형태입니다.

</def>
<def title="Q) groupBy 가 LinkedHashMap 을 쓰는 이유는 무엇인가요?">

키의 순서를 예측 가능하게 만들기 위해서입니다. `LinkedHashMap`은 삽입 순서를 보존하므로, 결과 맵의 키는 원본 컬렉션에서 각 키가 처음 등장한 순서대로 나열됩니다. 같은 입력에 대해 항상 같은 순서가 나온다는 뜻입니다.

일반 `HashMap`이었다면 키 순서가 해시값에 따라 결정되어 직관과 어긋났을 것이고, 순서에 의존하는 코드나 테스트가 불안정해졌을 것입니다. 결과를 그대로 화면에 뿌리는 경우가 많은 만큼 실용적인 선택입니다.

</def>
<def title="Q) 길이가 다른 두 리스트를 zip 하면 어떻게 되나요?">

짧은 쪽 길이에 맞춰 잘립니다. `zip` 구현의 반복 조건이 `while (first.hasNext() && second.hasNext())` 이므로, 두 이터레이터 중 하나라도 소진되면 그 즉시 멈춥니다. 긴 쪽에 남은 요소는 버려지고 예외도 나지 않습니다.

초기 용량을 `minOf(...)`로 잡는 것도 같은 이유입니다. 결과 크기가 두 컬렉션 크기의 최솟값이 될 것을 알기 때문에 그만큼만 미리 확보합니다. 길이가 다를 수 있는 데이터를 다룬다면 잘려 나가는 쪽이 있는지 먼저 확인하는 편이 안전합니다.

</def>
<def title="Q) 변환 연산자들이 inline 인 이유는 무엇인가요?">

람다 객체 생성 비용을 없애기 위해서입니다. 인라인이 아니라면 `filter { ... }`를 호출할 때마다 람다를 담을 `Function` 객체가 만들어집니다. 인라인이면 컴파일러가 `filterTo`의 루프와 람다 본문을 호출 지점에 그대로 복사하므로, 손으로 쓴 `for` + `if` 와 거의 같은 바이트코드가 나옵니다.

부수 효과가 하나 더 있습니다. 람다가 호출 지점의 문맥을 그대로 물려받기 때문에, 인라인 람다 안에서는 `suspend` 함수나 `@Composable` 함수를 부를 수 있습니다. 일반 람다에서는 금지된 동작입니다. 코루틴 안에서 `map { }` 안에 `suspend` 호출을 넣을 수 있는 이유가 이것입니다.

</def>
<def title="Q) 변환 연산자를 여러 개 연결하면 어떤 비용이 발생하나요?">

단계마다 중간 리스트가 새로 생깁니다. `map().filter().map()`이라면 리스트가 세 개 만들어집니다. 각 연산자가 독립적으로 `ArrayList`를 만들어 채운 뒤 돌려주는 구조이기 때문입니다.

더 중요한 것은 앞 단계가 전부 끝나야 다음 단계가 시작된다는 점입니다. `(1..1000).map { }.first()` 는 첫 원소만 필요한데도 람다를 1,000번 호출합니다. 같은 코드에 `asSequence()`를 넣으면 1번으로 줄어듭니다. `Sequence`는 원소 하나를 끝까지 흘려보내는 방식이라 중간 리스트를 만들지 않고 필요한 만큼만 계산하기 때문입니다.

원소가 수십 개 수준이면 차이가 없으므로 그대로 쓰는 편이 읽기 좋고, 컬렉션이 크거나 앞쪽 일부만 필요한 경우에 `asSequence()`를 고려하면 됩니다.

</def>
</deflist>
