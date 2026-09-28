# Q26) Iterator

`Iterator`는 컬렉션의 내부 구조를 드러내지 않고 요소를 **하나씩 차례로** 꺼내 주는 객체입니다. 배열이든 연결 리스트든 해시 테이블이든, 바깥에서는 "다음 게 있나?", "다음 걸 줘" 두 가지만 물으면 됩니다.

코틀린 컬렉션 API는 이 인터페이스를 기반으로 동작합니다. `for` 루프, Q25의 `mapTo`·`filterTo`, `zip`, 그리고 Q27의 `Sequence`까지 모두 내부에서 `Iterator`로 요소를 하나씩 꺼냅니다.

## Iterator 인터페이스 {#interface}

인터페이스 자체는 함수 두 개가 전부입니다.

```kotlin
// Iterator.kt
public interface Iterator<out T> {
    // 다음 요소를 반환합니다. 없으면 NoSuchElementException 을 던집니다.
    public operator fun next(): T

    // 남은 요소가 있으면 true 를 반환합니다.
    public operator fun hasNext(): Boolean
}
```

두 함수의 역할은 분명히 나뉩니다.

`hasNext()`는 **확인만** 합니다. 남은 요소가 있으면 `true`, 다 봤으면 `false`를 돌려주고, 커서는 움직이지 않습니다. 그래서 여러 번 불러도 결과가 같습니다.

`next()`는 **요소를 꺼내면서 커서를 다음 위치로 옮깁니다**. 이미 끝에 도달했는데 `next()`를 부르면 `NoSuchElementException`이 납니다.

```kotlin
// NextAfterEnd.kt
val it = listOf(1).iterator()
it.next()   // 1
it.next()   // NoSuchElementException
```

그래서 두 함수는 거의 항상 짝으로 씁니다. `hasNext()`로 확인하고, `true`일 때만 `next()`를 부르는 형태입니다.

```kotlin
// IteratorExample.kt
val names = listOf("skydoves", "kotlin", "developer")
val iterator = names.iterator()

while (iterator.hasNext()) {
    println(iterator.next())
}
```

`Iterator`는 **앞으로만 갈 수 있고, 한 번 끝까지 돌면 다시 쓸 수 없습니다.** 처음부터 다시 돌려면 컬렉션에 `iterator()`를 한 번 더 호출해 새 이터레이터를 받으면 됩니다. 컬렉션은 이터레이터를 몇 개든 만들어 줄 수 있고, 각 이터레이터는 자기 커서를 따로 갖습니다.

## 커서의 위치 {#cursor}

"커서를 다음 위치로 옮긴다"는 말은 두 가지로 읽힐 수 있습니다. 커서가 **지금 요소**를 가리키고 있다가 그다음 요소를 꺼내는 것인지, 커서가 가리키는 요소를 꺼낸 뒤 옮기는 것인지입니다.

기준이 되는 모델은 **커서가 요소와 요소 사이에 있다**는 것입니다. 자바 `ListIterator` 공식 문서도 이 모델로 설명합니다.

![Iterator 의 커서 위치](iterator-cursor.svg)

- 처음 만들어진 이터레이터의 커서는 **첫 요소 앞**에 있습니다. 그래서 첫 `next()`가 첫 요소를 돌려줍니다.
- `next()`는 커서 **바로 뒤 요소**를 돌려주고, 커서를 그 요소 뒤로 옮깁니다.
- `hasNext()`는 커서 뒤에 요소가 남아 있는지만 확인합니다. 마지막 요소 뒤에 도달하면 `false`입니다.

"지금 요소의 다음 요소를 꺼낸다"로 이해하면 첫 요소를 건너뛰게 되므로 틀린 모델입니다. 커서가 **다음에 돌려줄 요소**를 가리킨다고 생각해도 결과는 같습니다.

이 동작은 `Iterator`가 약속하는 **바깥에서 보이는 동작**이고, 내부에서 커서를 어떻게 기억하는지는 컬렉션마다 다릅니다.

![컬렉션별 커서 구현](iterator-implementations.svg)

- `ArrayList`는 커서를 **정수 인덱스 하나**(`cursor`)로 기억합니다. 처음 값은 0이고, `next()`는 `elementData[cursor]`를 돌려준 뒤 `cursor`를 1 늘립니다.
- `LinkedList`는 인덱스 대신 **다음 노드의 참조**(`next`)를 들고 있습니다. `next()`는 그 노드의 값을 돌려주고 `next = next.next`로 한 칸 넘어갑니다.
- `HashMap`은 내부 배열(버킷)에 빈칸이 섞여 있습니다. 그래서 이터레이터를 만들 때 **비어 있지 않은 첫 칸을 미리 찾아 두고**, `next()`로 그 요소를 돌려줄 때마다 다음으로 비어 있지 않은 칸을 다시 찾아 둡니다.
- 코틀린의 `1..10` 같은 범위는 요소를 저장하지 않습니다. 다음에 돌려줄 값과 증가폭만 들고 있다가 `next()`마다 값을 계산합니다.

저장 방식이 이렇게 달라도 "첫 `next()`는 첫 요소, 끝에서 `next()`는 `NoSuchElementException`"이라는 약속은 똑같이 지킵니다. 그래서 `for` 루프는 어떤 컬렉션이든 같은 코드로 순회할 수 있습니다. 인터페이스가 하는 일이 바로 이것입니다.

## for 루프의 변환 {#for-loop}

`for (x in xs)`는 짧게 쓰기 위한 표기일 뿐, 따로 동작하는 특별한 기능이 아닙니다. 컴파일러가 이 코드를 `iterator()`, `hasNext()`, `next()`를 호출하는 `while` 루프로 바꿔서 컴파일합니다.

```kotlin
// ForLoop.kt
for (name in names) {
    println(name)
}

// 컴파일러가 만드는 형태
val iterator = names.iterator()
while (iterator.hasNext()) {
    val name = iterator.next()
    println(name)
}
```

`List`를 순회하는 함수를 컴파일해 바이트코드를 보면 이 세 호출이 그대로 들어 있습니다.

```text
// javap -c 로 본 for (n in names)
invokeinterface java/util/List.iterator
invokeinterface java/util/Iterator.hasNext
invokeinterface java/util/Iterator.next
```

예외도 있습니다. **배열과 정수 범위는 이터레이터를 쓰지 않습니다.** `for (n in intArray)`는 `arraylength`와 인덱스 비교(`if_icmpge`)로, `for (i in 1..3)`는 정수 카운터 루프로 컴파일됩니다. 이터레이터 객체를 만들지 않도록 컴파일러가 최적화한 결과입니다. 이터레이터를 쓰는 것은 `List`, `Set` 같은 `Iterable` 타입입니다.

## operator 규약 {#operator-convention}

`Iterator`의 두 함수에는 `operator`가 붙어 있습니다. `for` 루프가 이 함수들을 이름으로 찾아 호출하기 때문입니다. 같은 이유로 `for` 루프는 `Iterable` 인터페이스를 요구하지 않습니다. **`operator fun iterator()`만 있으면** 어떤 타입이든 `for`로 순회할 수 있습니다.

```kotlin
// Countdown.kt
class Countdown(private val from: Int) {
    operator fun iterator() = object : Iterator<Int> {
        private var current = from
        override fun hasNext() = current > 0
        override fun next() = current--
    }
}

for (n in Countdown(3)) print("$n ")   // 3 2 1
```

`Countdown`은 `Iterable`을 구현하지 않았지만 `for`가 동작합니다. 컴파일러는 타입이 어떤 인터페이스를 구현했는지 보지 않고, `operator`가 붙은 `iterator()` 함수가 있는지만 확인하기 때문입니다. 확장 함수로 `operator fun iterator()`를 붙여도 마찬가지입니다. Q27의 `Sequence`도 `Iterable`이 아니지만 `iterator()` 하나로 순회됩니다.

## MutableIterator {#mutable-iterator}

`Iterator`는 읽기 전용입니다. 순회하면서 요소를 지워야 할 때는 `MutableIterator`를 씁니다. `MutableList`, `MutableSet` 등의 `iterator()`가 이 타입을 돌려줍니다.

```kotlin
// MutableIterator.kt
public interface MutableIterator<out T> : Iterator<T> {
    // next() 로 마지막에 반환한 요소를 컬렉션에서 제거합니다.
    public fun remove(): Unit
}
```

`remove()`는 인자를 받지 않습니다. **방금 `next()`가 돌려준 요소**를 지웁니다. 그래서 순서 제약이 있습니다.

- `next()`를 한 번도 부르지 않고 `remove()`를 부르면 `IllegalStateException`입니다. 지울 대상이 없습니다.
- `remove()`를 연달아 두 번 부르면 역시 `IllegalStateException`입니다. 한 번 지운 뒤에는 `next()`로 다음 요소를 받아야 다시 지울 수 있습니다.

올바른 순서는 `next()`로 꺼내고, 조건을 확인하고, 필요하면 `remove()`로 지우는 것입니다.

```kotlin
// RemoveEven.kt
val numbers = mutableListOf(1, 2, 3, 4, 5, 6, 7, 8)
val iterator = numbers.iterator()

while (iterator.hasNext()) {
    val number = iterator.next()
    if (number % 2 == 0) {
        iterator.remove()
    }
}

println(numbers)   // [1, 3, 5, 7]
```

이터레이터를 통해 지우면 이터레이터가 커서 위치를 알맞게 조정하므로 루프가 끝까지 문제없이 진행됩니다.

## ConcurrentModificationException {#cme}

같은 작업을 `for` 루프 안에서 리스트의 `remove()`를 직접 호출해서 하면 문제가 생깁니다.

```kotlin
// ForEachRemove.kt
val numbers = mutableListOf(1, 2, 3, 4, 5, 6, 7, 8)
for (n in numbers) {
    if (n % 2 == 0) numbers.remove(n)   // ConcurrentModificationException
}
```

실행하면 2를 지운 직후 다음 `next()`에서 `ConcurrentModificationException`이 납니다. 원인은 `for` 루프가 내부에서 쓰는 이터레이터입니다. JVM의 `ArrayList`는 구조가 바뀔 때마다 `modCount`를 올리고, 이터레이터는 만들어질 때의 값을 기억해 두었다가 `next()` 때마다 비교합니다. 이터레이터를 거치지 않고 리스트를 바꾸면 두 값이 어긋나고, 이터레이터는 "내가 모르는 사이에 컬렉션이 바뀌었다"고 판단해 예외를 던집니다.

이 예외는 **항상 발생한다고 보장되지 않습니다.** 검사는 `next()`를 호출할 때만 일어나므로, 지운 뒤 `hasNext()`가 `false`가 되어 루프가 먼저 끝나면 예외 없이 지나갑니다.

```kotlin
// NoException.kt
val list = mutableListOf(1, 2, 3)
for (x in list) if (x == 2) list.remove(x)
println(list)   // [1, 3] — 예외 없음, 3 은 확인하지 않고 끝남
```

끝에서 두 번째 요소를 지우면 크기가 줄어 `hasNext()`가 바로 `false`가 되고, 마지막 요소는 아예 검사하지 않고 끝납니다. 예외가 안 났다고 올바르게 동작한 것이 아닙니다.

실무에서 조건부 삭제는 대부분 `removeAll { }`(또는 `removeIf`) 한 줄로 충분합니다. 순회와 삭제를 함수 안에서 안전하게 처리해 줍니다.

```kotlin
// RemoveAll.kt
val numbers = mutableListOf(1, 2, 3, 4)
numbers.removeAll { it % 2 == 0 }
println(numbers)   // [1, 3]
```

`MutableIterator`를 직접 쓸 일은 한 번 순회하면서 삭제와 다른 작업을 같이 해야 할 때 정도입니다.

## 읽기 전용 리스트와 MutableIterator {#read-only-list}

Q24에서 본 것처럼 코틀린의 읽기 전용 인터페이스는 컴파일할 때만 적용되는 제약입니다. 이터레이터도 같습니다.

```kotlin
// ReadOnlyIterator.kt
val list = listOf(1, 2, 3)
println(list.iterator() is MutableIterator<*>)   // true
```

JVM에서는 `Iterator`와 `MutableIterator`가 모두 `java.util.Iterator` 하나로 매핑되므로 타입 검사로는 구별되지 않습니다. 그래서 캐스팅으로 `remove()`까지는 부를 수 있지만, `listOf(1, 2, 3)`의 실제 구현(`Arrays.asList` 기반)이 삭제를 지원하지 않아 `UnsupportedOperationException`이 납니다. 즉 `remove()`를 못 부르게 막는 것은 컴파일러의 타입 검사이고, 실행 중인 객체가 막아 줄 거라고 기대하면 안 됩니다.

## 요약 {#summary}

`Iterator`는 `hasNext()`와 `next()` 두 함수로 컬렉션 순회를 표현하는 인터페이스입니다. `hasNext()`는 상태를 바꾸지 않고 확인만 하며, `next()`는 요소를 꺼내면서 커서를 옮깁니다. 커서는 요소 사이에 있고 처음엔 첫 요소 앞이므로, 첫 `next()`는 첫 요소를 돌려줍니다. 끝에서 `next()`를 부르면 `NoSuchElementException`이 납니다. 커서를 기억하는 방식은 인덱스(`ArrayList`), 노드 참조(`LinkedList`), 미리 찾아 둔 칸(`HashMap`)처럼 컬렉션마다 다르지만 바깥 동작은 같습니다.

`for` 루프는 `iterator()`·`hasNext()`·`next()` 호출로 컴파일됩니다. 단, 배열과 정수 범위는 인덱스 루프로 최적화됩니다. `operator fun iterator()`만 있으면 `Iterable`이 아닌 타입도 `for`로 돌 수 있습니다.

순회 중 삭제에는 `MutableIterator.remove()`를 씁니다. 방금 `next()`가 준 요소를 지우므로 `next()` 없이 부르거나 두 번 연달아 부르면 `IllegalStateException`입니다. `for` 안에서 컬렉션을 직접 수정하면 `ConcurrentModificationException`이 나는데, 이 예외는 항상 나는 것이 아니므로 예외가 없었다고 안전한 것은 아닙니다. 단순한 조건부 삭제는 `removeAll { }`이 가장 간단합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) hasNext() 와 next() 는 각각 어떤 역할을 하나요?">

`hasNext()`는 남은 요소가 있는지 확인만 합니다. 커서를 움직이지 않으므로 여러 번 불러도 결과가 같습니다. `next()`는 현재 요소를 돌려주면서 커서를 다음 위치로 옮깁니다.

이미 끝에 도달한 상태에서 `next()`를 부르면 `NoSuchElementException`이 납니다. 그래서 `while (it.hasNext()) { it.next() }`처럼 확인한 뒤 꺼내는 형태로 짝지어 씁니다.

</def>
<def title="Q) next() 를 처음 호출하면 어떤 요소가 반환되나요?">

첫 요소가 반환됩니다. 새로 만든 이터레이터의 커서는 첫 요소 앞에 있고, `next()`는 커서 바로 뒤 요소를 돌려준 뒤 커서를 그 요소 뒤로 옮기기 때문입니다.

커서를 어떻게 기억하는지는 컬렉션마다 다릅니다. `ArrayList`는 0부터 시작하는 정수 인덱스, `LinkedList`는 다음 노드의 참조, `HashMap`은 미리 찾아 둔 비어 있지 않은 다음 칸을 씁니다. 하지만 바깥에서 보이는 동작은 모두 같습니다.

</def>
<def title="Q) for 루프는 내부적으로 어떻게 동작하나요?">

`List`나 `Set` 같은 `Iterable`에 대한 `for`는 컴파일러가 `iterator()`로 이터레이터를 받고, `hasNext()`가 `true`인 동안 `next()`로 요소를 꺼내는 `while` 루프로 바꿔서 컴파일합니다. 바이트코드에도 세 호출이 그대로 나타납니다.

배열과 `1..3` 같은 정수 범위는 예외입니다. 이터레이터 객체를 만들지 않고 인덱스나 카운터를 비교하는 루프로 컴파일됩니다. 또 `for`는 `Iterable`을 요구하지 않고 `operator fun iterator()`만 있으면 되므로, 직접 만든 타입도 이 함수를 정의하면 `for`로 순회할 수 있습니다.

</def>
<def title="Q) MutableIterator 의 remove() 에는 어떤 제약이 있나요?">

`remove()`는 인자 없이 "방금 `next()`가 돌려준 요소"를 지웁니다. 그래서 `next()`를 한 번도 부르지 않았거나, `remove()` 직후 `next()` 없이 다시 `remove()`를 부르면 지울 대상이 없어 `IllegalStateException`이 납니다.

올바른 패턴은 `next()`로 꺼내고, 조건을 판단하고, 필요하면 `remove()`를 부르는 순서입니다. 이터레이터를 통해 지우면 이터레이터가 커서를 알맞게 조정하므로 순회가 끝까지 안전하게 진행됩니다.

</def>
<def title="Q) for 루프 안에서 리스트의 요소를 지우면 왜 문제가 되나요?">

`for`가 내부에 이터레이터를 쓰고 있기 때문입니다. `ArrayList`는 구조가 바뀔 때마다 `modCount`를 올리고, 이터레이터는 `next()` 때마다 자기가 기억한 값과 비교합니다. 이터레이터를 거치지 않고 리스트를 직접 바꾸면 값이 어긋나 `ConcurrentModificationException`이 납니다.

이 예외가 항상 나는 것은 아닙니다. 지운 뒤 `hasNext()`가 먼저 `false`가 되면 예외 없이 끝나고, 그 경우 뒤쪽 요소가 검사되지 않고 지나갈 수 있습니다. 순회 중 삭제는 `MutableIterator.remove()`를 쓰거나, 단순한 조건이면 `removeAll { }`을 쓰는 것이 맞습니다.

</def>
</deflist>
