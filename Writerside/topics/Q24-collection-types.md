# Q24) 컬렉션 타입

코틀린은 요소 묶음을 다루기 위해 `List`, `Set`, `Map` 세 가지 컬렉션을 제공합니다. 그리고 각각이 **읽기 전용**과 **가변** 두 갈래로 나뉩니다.

자바에는 이 구분이 없습니다. `java.util.List` 하나뿐이고, 고쳐도 되는지 아닌지는 문서나 관례로만 전해집니다. 코틀린은 이것을 타입으로 끌어올렸습니다.

다만 이름만 보고 `List`를 "못 고치는 컬렉션"이라고 이해하면 틀립니다. 이 문서의 절반은 그 오해를 푸는 데 씁니다.

## 읽기 전용 컬렉션 {#read-only}

읽기 전용 컬렉션은 요소에 **접근하는** 연산만 제공합니다. 조회하는 메서드는 있지만 수정하는 메서드가 아예 없습니다.

```kotlin
// ReadOnlyCollections.kt
val readOnlyList = listOf("skydoves", "kotlin", "developer")
println(readOnlyList[0])        // skydoves

val readOnlySet = setOf("kotlin", "java", "kotlin")
println(readOnlySet)            // [kotlin, java]

val readOnlyMap = mapOf("language" to "kotlin", "platform" to "android")
println(readOnlyMap["language"]) // kotlin
```

`List`는 순서가 있고 인덱스로 접근합니다. `Set`은 중복을 허용하지 않습니다. `Map`은 키와 값의 쌍이고 키가 고유합니다.

여기서 하나 짚어 둘 것이 있습니다. `Set`과 `Map`은 **넣은 순서를 유지합니다.**

```kotlin
println(setOf(3, 1, 2))             // [3, 1, 2]
println(mapOf("c" to 3, "a" to 1))  // {c=3, a=1}
```

자바의 `HashSet`을 떠올리고 순서가 뒤섞일 것이라 예상하면 어긋납니다. 내부 구현이 `LinkedHashSet`과 `LinkedHashMap`이기 때문입니다.

## 가변 컬렉션 {#mutable}

가변 컬렉션은 요소를 추가·삭제·수정할 수 있습니다. 대응하는 읽기 전용 인터페이스를 **상속**하고 거기에 변경용 메서드를 더한 구조입니다.

```kotlin
interface List<out E> : Collection<E>
interface MutableList<E> : List<E>, MutableCollection<E>
```

```kotlin
// MutableCollections.kt
val mutableList = mutableListOf("skydoves", "kotlin")
mutableList.add("developer")
println(mutableList)   // [skydoves, kotlin, developer]

val mutableSet = mutableSetOf("kotlin", "java")
mutableSet.add("android")
println(mutableSet)    // [kotlin, java, android]

val mutableMap = mutableMapOf("language" to "kotlin")
mutableMap["platform"] = "android"
println(mutableMap)    // {language=kotlin, platform=android}
```

`MutableList`가 `List`를 상속하므로 `List` 자리에 넣을 수 있습니다. 함수 파라미터를 `List`로 선언하면 "이 컬렉션을 고치지 않겠다"는 선언이 됩니다.

```kotlin
fun show(items: List<String>) {
    // items.add(...) 는 컴파일되지 않는다
}
```

## 읽기 전용이 불변은 아닌 이유 {#not-immutable}

여기가 핵심입니다. `List`는 **불변**(immutable)이 아니라 **읽기 전용**(read-only)입니다.

불변이라면 값이 절대 안 바뀌어야 합니다. 읽기 전용은 **이 참조로는 못 고친다**는 뜻일 뿐입니다. 같은 객체를 가리키는 다른 참조가 있으면 그쪽에서 바뀝니다.

```kotlin
// Mutability.kt
val mutableList: MutableList<String> = mutableListOf("A", "B", "C")
val readOnlyList: List<String> = mutableList

// 읽기 전용 참조로는 수정할 수 없습니다.
// readOnlyList.add("D")   // 컴파일 오류

// 그러나 가변 참조를 고치면 읽기 전용 쪽에 그대로 반영됩니다.
mutableList.add("D")
println(readOnlyList)      // [A, B, C, D]

// 캐스팅으로도 뚫립니다.
(readOnlyList as MutableList<String>).add("E")
println(readOnlyList)      // [A, B, C, D, E]
```

`readOnlyList`는 아무 일도 하지 않았는데 내용이 두 번 바뀌었습니다. 둘이 같은 객체이기 때문입니다.

## 바이트코드에서의 동일성 {#bytecode}

캐스팅이 통하는 이유는 컴파일 결과를 보면 드러납니다. `List`와 `MutableList`는 **컴파일되면 같은 타입**입니다.

```kotlin
// Signatures.kt
fun readOnly(x: List<Int>) {}
fun mutable(x: MutableList<Int>) {}
```

```
$ javap -p SignaturesKt
public final class SignaturesKt {
  public static final void readOnly(java.util.List<java.lang.Integer>);
  public static final void mutable(java.util.List<java.lang.Integer>);
}
```

둘 다 `java.util.List`로 찍힙니다. 코틀린의 `List`와 `MutableList`는 새로 만든 클래스가 아니라 **자바 컬렉션에 씌운 타입 뷰**입니다. JVM 수준에는 이 구분이 존재하지 않습니다.

그래서 이 구분은 **컴파일러가 지켜 주는 약속**이지 런타임이 막아 주는 벽이 아닙니다. 컴파일러를 우회하면 그대로 뚫립니다.

## 자바와의 경계 {#java-interop}

가장 실질적인 구멍은 자바입니다. 코틀린이 읽기 전용이라고 선언한 리스트를 자바는 그냥 고칩니다.

```kotlin
// Lib.kt
object Lib {
    val names: List<String> = mutableListOf("a", "b")
}
```

```java
// Breaker.java
List<String> ro = Lib.INSTANCE.getNames();   // 코틀린에선 읽기 전용
ro.add("자바가 넣은 값");                      // 자바는 그냥 넣는다
System.out.println(ro);
```

```
자바에서 본 값: [a, b, 자바가 넣은 값]
```

예외도 경고도 없습니다. 자바 입장에서는 그냥 `java.util.List`라 막을 근거가 없습니다.

안드로이드처럼 자바 라이브러리와 섞이는 환경이라면 이 점이 중요합니다. 밖으로 나가는 컬렉션은 복사본을 넘기는 편이 안전합니다.

## 팩토리 함수가 고르는 구현 {#factory}

`listOf`는 상황에 따라 다른 구현을 돌려줍니다.

```kotlin
println(listOf<Int>()::class.java.name)       // kotlin.collections.EmptyList
println(listOf(1)::class.java.name)           // java.util.Collections$SingletonList
println(listOf(1, 2, 3)::class.java.name)     // java.util.Arrays$ArrayList
println(mutableListOf(1)::class.java.name)    // java.util.ArrayList
```

원소 수에 따라 가벼운 구현을 골라 씁니다. 그리고 이들은 캐스팅해도 못 고칩니다.

```kotlin
val fixed = listOf(1, 2, 3)
(fixed as MutableList<Int>).add(4)   // UnsupportedOperationException
```

앞 절에서 캐스팅이 통했던 것과 결과가 다릅니다. 그쪽은 실제 객체가 `ArrayList`였고, 이쪽은 `Arrays$ArrayList`라 `add`가 구현되어 있지 않기 때문입니다.

즉 **캐스팅이 먹히는지는 타입이 아니라 실제 객체에 달려 있습니다.** 선언만 봐서는 알 수 없습니다. 캐스팅에 기대면 안 되는 이유가 여기 있습니다.

## 완전한 불변성 확보 {#immutability}

값이 절대 안 바뀌는 것을 보장하려면 언어 기능만으로는 부족합니다. 선택지는 둘입니다.

**방어적 복사.** 받거나 넘길 때 새 컬렉션으로 복사합니다. 가장 간단하고 대부분의 경우 충분합니다.

```kotlin
class Repo(items: List<String>) {
    private val items = items.toList()          // 복사본을 들고 있는다
    fun all(): List<String> = items.toList()    // 복사본을 내보낸다
}
```

**kotlinx.collections.immutable.** `PersistentList` 같은 진짜 불변 컬렉션을 제공합니다. 수정하면 원본을 두고 새 컬렉션을 돌려줍니다. Q52에서 다룹니다.

Jetpack Compose를 쓴다면 이것이 성능과도 얽힙니다. `List`는 컴파일러가 안정적(stable)이라고 판단하지 못해 불필요한 재구성을 부를 수 있습니다. Compose 환경에서 `ImmutableList`를 권하는 이유 중 하나입니다.

## 요약 {#summary}

코틀린은 `List`·`Set`·`Map`을 읽기 전용과 가변 두 갈래로 제공합니다. 읽기 전용은 데이터 무결성을, 가변은 유연성을 줍니다. 기본은 읽기 전용으로 두고 정말 바뀌어야 하는 곳에만 가변을 쓰는 것이 안전합니다.

다만 읽기 전용은 불변이 아닙니다. 이 참조로 못 고칠 뿐, 같은 객체를 가리키는 가변 참조나 캐스팅, 자바 호출로는 바뀝니다. 바이트코드에서 둘 다 `java.util.List`이기 때문입니다. 완전한 불변성이 필요하면 방어적 복사나 `kotlinx.collections.immutable`을 써야 합니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 읽기 전용 컬렉션과 불변 컬렉션은 어떻게 다른가요?">

불변은 값이 절대 바뀌지 않는 것을 뜻하고, 읽기 전용은 그 참조로 고칠 수 없다는 뜻입니다. 코틀린의 `List`는 후자입니다. `MutableList`를 `List` 타입 변수에 담으면 그 변수로는 `add`를 부를 수 없지만, 원래의 가변 참조로 고치면 읽기 전용 쪽에도 그대로 반영됩니다. 같은 객체를 두 이름으로 보고 있을 뿐이기 때문입니다.

그래서 `List`를 받았다고 해서 내용이 고정되어 있다고 가정하면 안 됩니다. 특히 다른 곳에서 만든 컬렉션을 넘겨받아 오래 들고 있어야 한다면, 넘겨받는 시점에 `toList()`로 복사해 두는 편이 안전합니다.

</def>
<def title="Q) List 를 MutableList 로 캐스팅하면 항상 수정할 수 있나요?">

아닙니다. 실제 객체가 무엇이냐에 달려 있습니다. `mutableListOf`로 만든 뒤 `List` 타입에 담아 둔 것이라면 실제 객체가 `ArrayList`이므로 캐스팅 후 수정이 됩니다. 반면 `listOf(1, 2, 3)`으로 만든 것은 실제 객체가 `java.util.Arrays$ArrayList`인데, 여기에는 `add`가 구현되어 있지 않아 `UnsupportedOperationException`이 납니다.

즉 캐스팅의 성공 여부를 타입 선언만 보고 예측할 수 없습니다. 어느 쪽이든 의도적으로 기대서는 안 되는 동작이고, 수정이 필요하면 처음부터 `MutableList`로 선언하거나 `toMutableList()`로 복사본을 만들어야 합니다.

</def>
<def title="Q) 코틀린의 List 와 MutableList 는 바이트코드에서 어떻게 표현되나요?">

둘 다 `java.util.List`로 컴파일됩니다. `fun readOnly(x: List<Int>)`와 `fun mutable(x: MutableList<Int>)`를 컴파일해 `javap`으로 보면 시그니처가 완전히 같습니다. 코틀린의 컬렉션 인터페이스는 새로 만든 클래스가 아니라 기존 자바 컬렉션에 씌운 타입 뷰이기 때문입니다.

이것이 시사하는 바는 명확합니다. 읽기 전용이라는 제약은 컴파일 시점에만 존재합니다. 런타임에는 아무 표시도 남지 않으므로 캐스팅, 리플렉션, 자바 코드 어느 쪽으로든 우회할 수 있습니다.

</def>
<def title="Q) 자바 코드가 코틀린의 읽기 전용 컬렉션을 수정할 수 있나요?">

가능합니다. 코틀린에서 `List<String>`으로 노출한 프로퍼티를 자바에서 받으면 평범한 `java.util.List`로 보이고, `add`를 호출하면 그대로 들어갑니다. 예외도 경고도 없습니다. 실제 객체가 `ArrayList`라면 자바 입장에서 막을 이유가 전혀 없기 때문입니다.

안드로이드처럼 자바 라이브러리와 코드가 섞이는 환경에서는 실질적인 위험입니다. 외부로 컬렉션을 노출할 때는 `toList()`로 복사본을 넘기거나 `kotlinx.collections.immutable`의 불변 컬렉션을 쓰는 것이 안전합니다.

</def>
<def title="Q) setOf 와 mapOf 는 요소의 순서를 유지하나요?">

유지합니다. `setOf(3, 1, 2)`는 `[3, 1, 2]`를 그대로 출력하고, `mapOf("c" to 3, "a" to 1)`도 넣은 순서대로 나옵니다. 내부 구현이 `LinkedHashSet`과 `LinkedHashMap`이라 삽입 순서를 보존하기 때문입니다.

자바의 `HashSet`·`HashMap`은 순서를 보장하지 않으므로, 자바 경험을 그대로 옮겨 오면 어긋나는 지점입니다. 다만 이것은 구현에서 비롯된 성질이고 `Set`·`Map` 인터페이스가 계약으로 보장하는 것은 아니므로, 순서가 논리적으로 중요하다면 `List`를 쓰거나 정렬을 명시하는 편이 의도가 분명합니다.

</def>
</deflist>
