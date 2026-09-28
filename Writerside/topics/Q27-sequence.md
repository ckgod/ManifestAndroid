# Q27) Sequence

`Sequence`는 `List`와 똑같이 `map`, `filter`, `take`를 이어 붙일 수 있는 타입입니다. 코드만 보면 구분이 안 될 정도로 비슷하지만, 실행 방식은 정반대입니다.

`Iterable`(`List`, `Set`)의 연산자는 **즉시** 실행되고, 단계마다 중간 컬렉션을 만듭니다(Q25). `Sequence`의 연산자는 **아무것도 실행하지 않고** 할 일만 쌓아 두었다가, 결과가 필요해지는 순간 요소를 하나씩 파이프라인 끝까지 흘려보냅니다.

## Sequence 인터페이스 {#interface}

`Sequence`의 정의는 함수 하나입니다.

```kotlin
// Sequence.kt
public interface Sequence<out T> {
    // 시퀀스의 값을 차례로 돌려주는 이터레이터를 반환합니다.
    public operator fun iterator(): Iterator<T>
}
```

`List`는 요소들을 이미 메모리에 담고 있는 **데이터**입니다. `Sequence`는 요소를 **만들어 낼 수 있는 방법**입니다. 약속하는 것은 "요청하면 `Iterator`를 주겠다"는 것뿐이고, 요소는 그 이터레이터의 `next()`가 불릴 때 비로소 만들어지거나 꺼내집니다.

이렇게 소비하는 쪽이 필요할 때 다음 요소를 요청하는 방식을 풀(pull) 기반이라고 합니다. 반대로 생산자가 요소를 소비자에게 밀어 넣는 방식은 푸시(push) 기반입니다. 지연 평가, 즉 필요해질 때까지 계산을 미루는 동작은 이 풀 기반 구조에서 나옵니다.

`Sequence`는 `Iterable`을 상속하지 않습니다. 그래도 `operator fun iterator()`가 있으므로 `for`로 돌 수 있습니다(Q26).

## Sequence 생성 {#creation}

만드는 방법은 네 가지가 흔합니다.

```kotlin
// SequenceCreation.kt
// 1. 값을 직접 나열
val a = sequenceOf(1, 2, 3)

// 2. 기존 컬렉션을 감싸기
val b = listOf(1, 2, 3).asSequence()

// 3. 앞 값으로 다음 값을 계산 — null 을 반환하면 끝
val c = generateSequence(1) { if (it < 5) it + 1 else null }

// 4. sequence 빌더 — yield 로 값을 하나씩 내보냄
val fibonacci = sequence {
    var x = 0; var y = 1
    while (true) {
        yield(x)
        val next = x + y
        x = y; y = next
    }
}
println(fibonacci.take(10).toList())   // [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

`fibonacci`는 `while (true)`로 끝나지 않는 **무한 시퀀스**입니다. 그래도 문제가 없는 이유는 `take(10)`이 10개만 요청하기 때문입니다. `yield`는 값을 하나 내보내고 다음 요청이 올 때까지 실행을 멈춥니다. 이 "멈췄다 이어서 실행"은 코루틴의 중단 메커니즘으로 구현되어 있으며, Chapter 2에서 다룹니다.

`List`로는 무한한 데이터를 표현할 수 없습니다. 모든 요소를 메모리에 담아야 하기 때문입니다. `Sequence`는 필요한 만큼만 만들어 내므로 가능합니다.

## 중간 연산의 구현 {#intermediate}

`Sequence`의 `map`이나 `filter`를 호출하면 무슨 일이 일어나는지 보면 지연 평가의 정체가 드러납니다. 호출 즉시 요소를 처리하지 않고, **원본 시퀀스와 수행할 연산을 감싼 새 `Sequence` 객체**를 돌려줄 뿐입니다.

개념적으로 쓰면 이렇습니다(실제 구현은 `TransformingSequence` 클래스입니다).

```kotlin
// SequenceMapConceptual.kt
fun <T, R> Sequence<T>.map(transform: (T) -> R): Sequence<R> =
    object : Sequence<R> {
        override fun iterator(): Iterator<R> = object : Iterator<R> {
            // 위쪽(원본) 시퀀스의 이터레이터
            val upstream = this@map.iterator()

            // 남은 게 있는지는 위쪽에 그대로 물어봄
            override fun hasNext() = upstream.hasNext()

            // 위쪽에서 하나 받아 그 하나에만 변환을 적용
            override fun next() = transform(upstream.next())
        }
    }
```

`map`은 순회도 계산도 하지 않습니다. "위쪽 이터레이터에서 하나 받아 `transform`을 적용하라"는 규칙을 가진 객체를 만들 뿐입니다. 실제로 중간 연산만 호출하고 끝내면 람다는 한 번도 실행되지 않습니다.

```kotlin
// LazyOnly.kt
val lazy = sequenceOf(1, 2, 3).map { println("실행됨 $it"); it }
println(lazy::class.java.simpleName)   // TransformingSequence — "실행됨" 은 한 줄도 출력되지 않음
```

연산을 이어 붙이면 이런 래퍼가 겹겹이 쌓입니다. `(1..10).asSequence().filter { }.map { }.take(2)`의 결과는 `TakeSequence`이고, 그 안에 `TransformingSequence`, 그 안에 `FilteringSequence`, 그 안에 원본이 들어 있는 양파 구조입니다. 각 층은 자기 연산 하나만 알고 있습니다.

`filter`는 `map`보다 조금 복잡합니다. `hasNext()`가 "다음 요소가 있느냐"에 답하려면 조건을 통과하는 요소가 실제로 있는지 알아야 하므로, `hasNext()` 안에서 **통과하는 요소를 찾을 때까지 미리 당겨 오고** 그 값을 저장해 둡니다. 그다음 `next()`는 저장해 둔 값을 돌려줍니다. 표준 라이브러리 `FilteringSequence`의 이터레이터가 `nextItem`·`nextState` 필드와 `calcNext()` 함수를 갖는 이유입니다.

## 종단 연산과 실행 흐름 {#terminal}

쌓아 둔 파이프라인은 **종단 연산**이 호출될 때 비로소 움직입니다. 종단 연산은 시퀀스가 아닌 결과를 돌려주는 함수로, `toList()`, `first()`, `count()`, `forEach()`, `sum()` 등이 있습니다.

종단 연산은 가장 바깥 시퀀스에 `iterator()`를 요청합니다. 그 이터레이터는 만들어지면서 안쪽 시퀀스의 이터레이터를 요청하고, 이렇게 원본까지 거슬러 올라갑니다. 그다음 바깥에서 `next()`를 부르면 요청이 안쪽으로 전달되고, 요소 하나가 원본에서 나와 각 층을 거쳐 밖으로 올라옵니다.

```kotlin
// SequenceExecution.kt
val result = (1..10).asSequence()
    .filter {
        println("Filtering $it")
        it % 2 == 0
    }
    .map {
        println("Mapping $it")
        it * 2
    }
    .take(2)
    .toList()

println("Result: $result")
```

```text
Filtering 1
Filtering 2
Mapping 2
Filtering 3
Filtering 4
Mapping 4
Result: [4, 8]
```

출력 순서가 실행 흐름을 그대로 보여 줍니다.

1. `toList()`가 `take` 층에 요소를 요청합니다. `take`는 `map`에, `map`은 `filter`에 요청을 넘깁니다.
2. `filter`가 원본에서 1을 꺼냅니다. 조건 실패입니다. 2를 꺼냅니다. 통과입니다.
3. 2가 `map`으로 올라가 4가 되고, `take`를 거쳐 결과 리스트에 들어갑니다.
4. 두 번째 요청에서 `filter`가 3(실패), 4(통과)를 꺼내고, `map`이 8로 바꿔 올립니다.
5. `take(2)`는 두 개를 채웠으므로 `hasNext()`가 `false`를 돌려주고 순회가 끝납니다.

원본 10개 중 **4개만** 꺼냈고, 5부터 10까지는 손도 대지 않았습니다.

같은 코드를 `List`로 돌리면 흐름이 완전히 다릅니다.

```text
// asSequence() 를 뺀 경우
F1 F2 F3 F4 F5 F6 F7 F8 F9 F10 M2 M4 M6 M8 M10
Result: [4, 8]
```

`filter`가 10개를 전부 처리해 중간 리스트를 완성하고, 그다음 `map`이 5개를 전부 처리합니다. 결과는 같지만 `filter` 10회, `map` 5회로, 시퀀스(`filter` 4회, `map` 2회)보다 훨씬 많이 일합니다.

## 즉시 평가와 지연 평가의 차이 {#eager-vs-lazy}

두 실행 모델의 차이를 정리하면 이렇습니다.

| | `Iterable` (즉시 평가) | `Sequence` (지연 평가) |
|---|---|---|
| 처리 순서 | 단계별 — 한 연산이 모든 요소를 끝내야 다음 연산 | 요소별 — 한 요소가 모든 연산을 통과한 뒤 다음 요소 |
| 중간 결과 | 단계마다 새 `List` 생성 | 중간 컬렉션 없음 |
| 조기 종료 | 불가 — 앞 단계가 끝까지 돎 | 가능 — `take`, `first` 등에서 즉시 멈춤 |
| 무한 데이터 | 표현 불가 | 가능 |
| 연산자 | 대부분 `inline` | `inline` 아님 — 람다를 객체로 저장 |

마지막 줄이 중요합니다. 시퀀스의 `map`은 람다를 **나중에 실행하려고 저장해 둬야** 하므로 인라인될 수 없습니다. 그 결과 두 가지가 달라집니다.

첫째, 단계마다 람다 객체와 래퍼 시퀀스·이터레이터 객체가 생깁니다. 요소 하나를 꺼낼 때마다 층마다 `hasNext()`·`next()` 가상 호출도 일어납니다.

둘째, Q25에서 본 "인라인 람다는 호출 지점의 문맥을 물려받는다"는 이점이 사라집니다. `List`의 `map` 안에서는 `suspend` 함수를 부를 수 있지만, `Sequence`의 `map` 안에서는 컴파일 오류가 납니다.

```kotlin
// SuspendInSequence.kt
suspend fun load(x: Int) = x

suspend fun ok() = listOf(1).map { load(it) }                   // 컴파일됨
suspend fun ng() = sequenceOf(1).map { load(it) }.toList()      // 오류: suspension functions can only be called within coroutine body
```

## 상태를 가진 연산 {#stateful}

모든 중간 연산이 요소 하나씩 흘려보낼 수 있는 것은 아닙니다. `sorted()`는 가장 작은 요소를 알려면 **모든 요소를 봐야** 합니다.

```kotlin
// SortedIsNotLazy.kt
val first = sequenceOf(3, 1, 2)
    .map { println("map $it"); it }
    .sorted()
    .first()
// map 3
// map 1
// map 2
println(first)   // 1
```

`first()`로 하나만 원했는데 `map`이 세 번 모두 실행됐습니다. `sorted()`는 반환 타입이 `Sequence`라 중간 연산이지만, 첫 요소를 요청받는 순간 위쪽을 끝까지 소비해 내부 리스트에 담고 정렬합니다. `sortedBy`, `distinct`처럼 전체를 보거나 지금까지 본 것을 기억해야 하는 연산은 이런 **상태를 가진(stateful)** 중간 연산입니다. 무한 시퀀스에 `sorted()`를 걸면 끝나지 않습니다.

## 한 번만 순회되는 시퀀스 {#constrain-once}

대부분의 시퀀스는 `iterator()`를 부를 때마다 처음부터 다시 계산하므로 여러 번 순회할 수 있습니다. 그런데 원본이 다시 시작할 수 없는 경우는 한 번만 순회되도록 막혀 있습니다.

```kotlin
// ConstrainOnce.kt
val once = generateSequence { readLine() }   // 초기값 없는 형태
once.toList()
once.toList()   // IllegalStateException: This sequence can be consumed only once.
```

초기값 없이 함수만 받는 `generateSequence { }`, 그리고 `Iterator.asSequence()`로 만든 시퀀스가 그렇습니다. 이터레이터나 외부 입력은 한 번 읽으면 되감을 수 없기 때문입니다. 반면 초기값을 받는 `generateSequence(1) { ... }`는 매번 처음부터 다시 생성하므로 여러 번 순회해도 같은 결과가 나옵니다.

## Sequence 를 쓸 때 {#when-to-use}

`Sequence`가 항상 빠른 것은 아닙니다. 층마다 객체와 가상 호출 비용이 있으므로, 요소가 수십 개 수준이고 모든 요소를 끝까지 처리하는 코드라면 인라인되는 `List` 연산자가 오히려 빠르고 읽기도 편합니다.

`Sequence`가 이득인 경우는 이렇습니다.

- 연산을 여러 단계 이어 붙이고 컬렉션이 커서 **중간 리스트 비용**이 부담될 때
- `first`, `take`, `find`, `any`처럼 **앞쪽 일부만** 필요해 조기 종료가 가능할 때
- 무한하거나 계산 비용이 커서 **필요한 만큼만** 만들어야 할 때

반대로 `sorted()`처럼 상태를 가진 연산이 앞에 있거나, 람다 안에서 `suspend` 함수를 불러야 하면 `List`가 맞습니다.

## 요약 {#summary}

`Sequence`는 `iterator()` 하나만 가진 인터페이스이고, 요소를 담은 데이터가 아니라 요소를 만들어 내는 방법을 나타냅니다. `map`, `filter` 같은 중간 연산은 아무것도 실행하지 않고 원본과 연산을 감싼 새 시퀀스(`TransformingSequence`, `FilteringSequence` 등)를 돌려주며, 이 래퍼들이 겹겹이 쌓여 파이프라인이 됩니다.

`toList()`, `first()` 같은 종단 연산이 호출되면 이터레이터 체인이 만들어지고, 요소가 하나씩 모든 단계를 통과합니다. 그래서 중간 컬렉션이 생기지 않고, `take`나 `first`에서 조기 종료되며, 무한 시퀀스도 다룰 수 있습니다.

대신 연산자가 인라인되지 않아 층마다 객체·호출 비용이 있고, 람다 안에서 `suspend` 함수를 부를 수 없습니다. `sorted()`·`distinct()`는 전체를 소비하는 상태 연산이며, 이터레이터나 외부 입력을 감싼 시퀀스는 한 번만 순회됩니다. 작은 컬렉션을 끝까지 처리할 때는 `List`, 크거나 앞쪽 일부만 필요하거나 무한한 데이터에는 `Sequence`가 맞습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Sequence 의 map 을 호출하면 내부적으로 무슨 일이 일어나나요?">

아무 요소도 처리하지 않습니다. 원본 시퀀스와 변환 함수를 담은 새 `Sequence` 객체(`TransformingSequence`)를 만들어 돌려줄 뿐입니다. 이 객체의 이터레이터는 `next()`가 불리면 위쪽 이터레이터에서 요소 하나를 받아 그 하나에만 변환을 적용합니다.

그래서 중간 연산만 이어 붙이고 종단 연산을 부르지 않으면 람다는 한 번도 실행되지 않습니다. `filter`, `take` 같은 다른 중간 연산도 같은 방식으로 래퍼를 하나씩 덧씌웁니다.

</def>
<def title="Q) List 와 Sequence 는 실행 순서가 어떻게 다른가요?">

`List`는 단계별로 처리합니다. `filter`가 모든 요소를 처리해 중간 리스트를 완성한 뒤에야 `map`이 시작됩니다. `Sequence`는 요소별로 처리합니다. 요소 하나가 `filter`와 `map`을 모두 통과한 뒤 다음 요소로 넘어갑니다.

`(1..10)`에 `filter { 짝수 }.map { *2 }.take(2)`를 걸면 `List`는 `filter` 10회, `map` 5회를 실행하지만 `Sequence`는 `filter` 4회, `map` 2회로 끝납니다. `take(2)`가 두 개를 채우는 순간 순회를 멈추고, 나머지 요소는 꺼내지도 않기 때문입니다.

</def>
<def title="Q) Sequence 가 List 보다 불리한 경우는 언제인가요?">

작은 컬렉션을 끝까지 처리하는 경우입니다. 시퀀스의 연산자는 람다를 저장해 두었다가 나중에 실행해야 하므로 인라인되지 않고, 단계마다 래퍼 객체와 이터레이터가 생기며 요소마다 층별 가상 호출이 일어납니다. 중간 리스트를 아끼는 이득이 없으면 이 비용만 남습니다.

또 인라인이 아니라서 `map` 람다 안에서 `suspend` 함수를 부를 수 없습니다. `sorted()`처럼 전체를 봐야 하는 상태 연산이 있으면 어차피 모든 요소를 소비하므로 지연 평가의 이점도 줄어듭니다.

</def>
<def title="Q) 한 번만 순회할 수 있는 시퀀스는 어떤 경우에 생기나요?">

원본을 되감을 수 없을 때입니다. 초기값 없이 함수만 받는 `generateSequence { }`나 `Iterator.asSequence()`로 만든 시퀀스가 대표적입니다. 이터레이터나 외부 입력은 한 번 읽으면 처음으로 돌아갈 수 없으므로, 두 번째 순회를 시도하면 `IllegalStateException`이 납니다.

반면 `sequenceOf`, `asSequence()`로 감싼 컬렉션, 초기값을 받는 `generateSequence(seed) { }`는 `iterator()`를 부를 때마다 처음부터 다시 계산하므로 여러 번 순회할 수 있습니다.

</def>
</deflist>
