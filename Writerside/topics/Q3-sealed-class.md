# Q3) sealed class와 sealed interface

`sealed class`는 서브클래스의 계층 구조를 제한하는 특수한 종류의 클래스입니다. 일반 클래스와 달리 **닫힌(closed) 타입 집합**을 정의하며, 직접 서브클래스는 같은 모듈·같은 패키지 안에만 존재할 수 있습니다. 그 덕분에 컴파일러가 직접 서브클래스 전부를 인지하며, 이 "컴파일러가 종류를 전부 안다"는 성질이 sealed가 주는 모든 장점의 뿌리입니다.

특정 옵션만 허용되는 상태나 결과를 모델링할 때 특히 유용합니다. 네트워크 응답(성공·실패·로딩), UI 상태처럼 경우의 수가 유한하게 정해진 것을 타입으로 못박는 데 적합합니다.

## sealed class의 핵심 특성 {#characteristics}

Sealed 클래스는 제한된 클래스 계층을 안전하게 표현하는 방법을 제공합니다. 주요 특성은 다음과 같습니다.

1. **닫힌 계층 구조** — 직접 서브클래스는 sealed class와 같은 모듈·패키지 안에서만 선언할 수 있다. 외부에서 새로운 종류를 추가할 수 없으므로, 계층이 유한하게 통제된다.
2. **`when` 완전성(exhaustiveness)** — 컴파일러가 모든 직접 서브클래스를 알기 때문에, `when`에서 한 케이스라도 빠지면 컴파일되지 않는다. sealed의 대표 기능이다.
3. **서브클래스 타입의 유연성** — 서브클래스는 일반 클래스, `data class`, `object`, `data object` 무엇이든 될 수 있다.

> **`enum`과의 차이** — `enum`도 정해진 값 집합을 표현하지만, 각 값은 동일한 형태의 상수일 뿐입니다. 반면 sealed의 서브클래스는 저마다 다른 프로퍼티를 가질 수 있습니다. `Success(val data)`는 데이터를, `Error(val message)`는 메시지를 담는 식입니다. "종류도 유한하고, 종류마다 담는 값도 다른" 상태를 표현할 때는 sealed가 적합합니다.

## 사용 사례와 예제 {#use-cases}

Sealed 클래스는 제한된 상태 집합을 명확하고 안전하게 모델링해야 하는 상황에서 잘 작동합니다. 대표적으로 **유한 상태 모델링**(로딩·성공·에러 등)과 **데이터 래핑**(다양한 데이터 타입을 타입 안전하게 감싸기)에 쓰입니다.

예를 들어 응답의 여러 상태를 표현하는 `Result`를 다음과 같이 정의할 수 있습니다.

```kotlin
sealed class Result {
    data class Success(val data: String) : Result()
    data class Error(val errorMessage: String) : Result()
    data object Loading : Result()
}

fun handleResult(result: Result) {
    when (result) {
        is Result.Success -> println("Data: ${result.data}")
        is Result.Error   -> println("Error: ${result.errorMessage}")
        Result.Loading    -> println("Loading...")
        // else 가지가 필요 없다 — 세 경우가 전부임을 컴파일러가 안다
    }
}
```

여기서 얻는 실질적 이득은 `else` 가지가 필요 없다는 점입니다. 나중에 `Result`에 `data object Empty`를 추가하면, 위 `when`은 컴파일 에러를 내며 "Empty 처리를 빠뜨렸다"고 알려 줍니다. 상태가 늘어날 때 처리 누락을 컴파일 시점에 잡아 주는 것이 sealed를 쓰는 핵심 이유입니다. 반면 일반 클래스는 어디서든 새 서브클래스를 만들 수 있어 이런 보장을 받을 수 없습니다.

> **`data object`란** — 값을 담지 않는 상태(예: `Loading`)는 인스턴스가 하나면 충분하므로 `object`로 선언합니다. 여기에 `data`를 붙인 `data object`(Kotlin 1.9)는 `toString()`을 `Loading`처럼 이름 그대로 출력해 주고 `equals()`·`hashCode()`도 일관되게 만들어 줍니다. 로깅 시 `Result$Loading@1a2b` 대신 `Loading`으로 보이는 차이입니다.

## sealed class와 sealed interface {#class-vs-interface}

Sealed 클래스와 sealed 인터페이스 모두 닫힌 타입 집합을 정의하지만, 상속 방식에서 차이가 있습니다.

- **sealed class** — 각 서브클래스가 클래스를 상속하므로 **단일 상속**만 가능하다. 엄격한 하나의 타입 계층을 표현하기에 적합하다.
- **sealed interface** (Kotlin 1.5) — 인터페이스이므로 한 클래스가 **여러 sealed interface를 동시에 구현**할 수 있다. 서로 독립적인 능력·역할을 조합해야 할 때 유연하다.

```kotlin
sealed interface Clickable { fun onClick() }
sealed interface Draggable { fun onDrag() }

// 한 클래스가 두 sealed interface를 모두 구현
class Button : Clickable, Draggable {
    override fun onClick() { println("Button clicked") }
    override fun onDrag()  { println("Button dragged") }
}
```

정리하면, sealed class는 "이 타입은 이런 모양이다"라고 구조를 강하게 고정할 때, sealed interface는 "이 타입들은 이 능력을 지켜야 한다"를 여러 갈래로 표현할 때 유용합니다. 두 경우 모두 `when`에서 완전성 검사가 되어 실수를 줄이고 코드 안정성을 높입니다.

> **닫힌 집합(closed set)이라는 표현** — 수학적으로는 "경계점을 모두 포함하는 집합"을 뜻하지만, 실무에서는 **"가능한 타입이 미리 다 정해져 있고 밖에서 더 늘릴 수 없는 집합"** 으로 이해하면 충분합니다. 컴파일러가 그 목록을 통째로 알기 때문에 `when` 완전성 검사가 가능한 것입니다.

## Pro Tips {#pro-tips}

### 서브클래스의 위치 제약과 완화 {#subclass-location}

sealed의 직접 서브클래스는 sealed 타입과 같은 모듈·같은 패키지 안에 있어야 합니다. 초기 Kotlin(1.1)에서는 **같은 파일** 안에만 허용됐지만, [Sealed Interface Freedom KEEP 제안](https://github.com/Kotlin/KEEP/blob/master/proposals/sealed-interface-freedom.md)을 거쳐 Kotlin 1.5부터 **같은 모듈·패키지라면 여러 파일에 나눠** 선언할 수 있도록 완화됐습니다. 대규모 프로젝트에서 확장성과 모듈성을 개선하기 위한 변경이며, "모든 구현이 같은 모듈에 있어야 한다"는 안전장치는 그대로 유지되어 `when` 완전성 검사의 이점을 잃지 않습니다.

### sealed class 상속 확장 논의 {#inheritance-keep}

[Sealed class 상속 KEEP 제안](https://github.com/Kotlin/KEEP/blob/master/proposals/sealed-class-inheritance.md)은 sealed class가 non-sealed 또는 open 상위 클래스로부터 **상속받을 수 있도록** 허용하는 방향을 논의합니다. 완전한 `when` 검사와 컴파일 타임 안전성을 유지하면서도 sealed class를 기존 계층 구조에 더 자연스럽게 통합하려는 시도로, 공유 추상화와의 결합 같은 사용 사례를 다룹니다. 아직 논의 단계이므로 상속 규칙과 런타임 동작에 대한 고려가 남아 있습니다.

## 요약 {#summary}

> **TL;DR** — `sealed`는 서브클래스가 같은 모듈·패키지 안에만 존재하도록 제한해, 컴파일러가 직접 서브클래스 전부를 알게 만듭니다. 덕분에 `when`에서 모든 경우를 강제(완전성)할 수 있어 상태가 늘 때 처리 누락을 컴파일 시점에 잡습니다. sealed class는 단일 상속(엄격한 계층), sealed interface는 다중 구현(유연한 조합)에 적합합니다.

1. **닫힌 계층**: 직접 서브클래스는 같은 모듈·패키지에만. 컴파일러가 종류를 전부 안다.
2. **`when` 완전성**: 모든 서브클래스를 다루지 않으면 컴파일 에러. `else` 없이 안전하게 분기하고, 케이스 추가 시 누락을 잡아 준다.
3. **`enum`과의 차이**: 서브클래스마다 다른 프로퍼티를 가질 수 있다(`Success(data)` vs `Error(message)`).
4. **class vs interface**: class는 단일 상속(엄격한 계층), interface(1.5)는 다중 구현(능력 조합).
5. **`data object`**: 값 없는 상태(`Loading`)를 하나뿐인 인스턴스 + 일관된 `toString()`으로 표현(1.9).

<deflist collapsible="true" default-state="collapsed">
<def title="Q) sealed class를 쓰면 무엇이 좋은가요?">

컴파일러가 직접 서브클래스 전부를 알기 때문에 `when` 표현식에서 **완전성(exhaustiveness) 검사**가 가능합니다. 모든 경우를 처리하지 않으면 컴파일이 되지 않고, `else` 가지 없이도 안전하게 분기할 수 있습니다. 특히 나중에 서브클래스(상태)를 추가하면 기존 `when`이 컴파일 에러를 내며 처리 누락을 알려 주므로, 상태가 늘어나는 코드를 안전하게 유지할 수 있습니다.

</def>
<def title="Q) sealed class와 enum class는 어떻게 다른가요?">

`enum`은 정해진 상수 집합을 표현하지만 각 값은 같은 형태를 가집니다. 반면 sealed class의 서브클래스는 저마다 다른 프로퍼티를 가질 수 있습니다. 예를 들어 `Success`는 데이터를, `Error`는 에러 메시지를 담을 수 있죠. "경우의 수도 유한하고, 경우마다 담는 데이터도 다른" 상태를 모델링할 때는 sealed가 적합합니다.

</def>
<def title="Q) sealed class와 sealed interface의 차이는 무엇인가요?">

가장 큰 차이는 상속 방식입니다. sealed class의 서브클래스는 클래스를 상속하므로 **단일 상속**만 가능해 엄격한 하나의 계층을 표현합니다. sealed interface(Kotlin 1.5)는 인터페이스라서 한 클래스가 **여러 sealed interface를 동시에 구현**할 수 있어, 독립적인 능력·역할을 조합할 때 유연합니다. 둘 다 `when` 완전성 검사의 이점은 동일하게 가집니다.

</def>
<def title="Q) sealed의 서브클래스는 어디에 선언해야 하나요?">

직접 서브클래스는 sealed 타입과 같은 모듈·같은 패키지 안에 있어야 합니다. 과거(1.1)에는 같은 파일 안에만 허용됐지만, Kotlin 1.5부터 같은 모듈·패키지라면 여러 파일에 나눠 선언할 수 있게 완화됐습니다. 이 제약 덕분에 컴파일러가 서브클래스 집합 전체를 컴파일 시점에 확정할 수 있습니다.

</def>
</deflist>
