# Q3) sealed class와 sealed interface

프로그램을 짜다 보면 "이 값은 A거나 B거나 C, 이 셋 중 하나다"라고 **가능한 경우를 미리 못박고 싶을 때**가 많습니다. 네트워크 응답은 성공/실패/로딩 중 하나고, 화면 상태는 로딩/완료/에러 중 하나죠. 이런 **닫힌(closed) 타입 집합**을 표현하는 것이 `sealed class`와 `sealed interface`입니다.

일반 클래스는 어디서든 새 서브클래스를 만들 수 있어 "종류가 몇 개인지" 컴파일러가 알 수 없습니다. 반면 `sealed`는 서브클래스가 **같은 모듈·같은 패키지 안에만** 존재할 수 있어, 컴파일러가 **직접 서브클래스 전부를 압니다**. 이 "컴파일러가 전부 안다"는 성질이 sealed의 모든 장점의 뿌리입니다.

## sealed class의 핵심 특성 {#characteristics}

- **닫힌 계층 구조**: 직접 서브클래스는 sealed class와 같은 모듈·패키지 안에서만 선언할 수 있다. 외부에서 몰래 새 종류를 추가할 수 없으므로, 계층이 유한하게 통제된다.
- **`when` 완전성(exhaustiveness)**: 컴파일러가 모든 직접 서브클래스를 알기 때문에, `when`에서 한 케이스라도 빠지면 **컴파일이 되지 않는다**. 이게 sealed의 킬러 기능이다.
- **서브클래스 타입의 유연성**: 서브클래스는 일반 클래스, `data class`, `object`, `data object` 무엇이든 될 수 있다.

> **`sealed`는 왜 `enum`보다 강력한가** — `enum`도 "정해진 값 집합"을 표현하지만, 각 값은 **동일한 형태의 상수**일 뿐입니다. sealed는 서브클래스마다 **다른 프로퍼티**를 가질 수 있습니다. `Success(val data)`는 데이터를, `Error(val message)`는 메시지를 담는 식으로요. "종류도 유한하고, 종류마다 담는 값도 다른" 상태를 표현할 때는 sealed가 정답입니다.

## 언제 쓰나 {#use-cases}

가장 흔한 두 쓰임새는 **유한 상태 모델링**과 **데이터 래핑**입니다. 네트워크 상태(loading·success·error), 사용자 입력, UI 상태처럼 "경우의 수가 정해진" 것을 타입으로 못박을 때 잘 맞습니다.

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
        // else 가 필요 없다 — 세 경우가 전부임을 컴파일러가 안다
    }
}
```

여기서 진짜 이득은 `else` 가지가 필요 없다는 점입니다. 나중에 `Result`에 `data object Empty`를 추가하면, 위 `when`은 **컴파일 에러**가 나면서 "Empty 처리를 빠뜨렸다"고 알려 줍니다. 상태가 늘어날 때 처리 누락을 컴파일 시점에 잡아 주는 것 — 이것이 sealed를 쓰는 핵심 이유입니다.

> **`data object`가 뭔가요** — 값을 담지 않는 상태(예: `Loading`)는 인스턴스가 하나면 충분하므로 `object`로 선언합니다. 여기에 `data`를 붙인 `data object`(Kotlin 1.9+)는 `toString()`을 `Loading`처럼 이름 그대로 예쁘게 찍어 주고 `equals()`/`hashCode()`도 일관되게 만들어 줍니다. 로깅·디버깅 시 `Result$Loading@1a2b` 대신 `Loading`으로 보이는 차이입니다.

## sealed class vs sealed interface {#class-vs-interface}

둘 다 "닫힌 집합"을 만든다는 목적은 같지만, **상속 방식**이 다릅니다.

- **sealed class** — 각 서브클래스가 클래스를 상속하므로 **단일 상속**만 가능. 엄격한 하나의 타입 계층을 표현하기 좋다.
- **sealed interface** (Kotlin 1.5+) — 인터페이스라서 한 클래스가 **여러 sealed interface를 동시에 구현**할 수 있다(다중 구현). 서로 독립적인 능력·역할을 조합할 때 유연하다.

```kotlin
// sealed interface: 독립적인 능력을 정의하고, 한 클래스가 둘 다 구현
sealed interface Clickable { fun onClick() }
sealed interface Draggable { fun onDrag() }

class Button : Clickable, Draggable {
    override fun onClick() { println("Button clicked") }
    override fun onDrag()  { println("Button dragged") }
}
```

한 문장으로 정리하면, **sealed class는 "이 타입은 이런 모양이다"라고 구조를 강하게 고정할 때**, **sealed interface는 "이 타입들은 이 규칙(능력)을 지켜야 한다"를 여러 갈래로 표현할 때** 유용합니다. 실무에서 상태 모델링에는 보통 sealed class(또는 interface)에 `data class`·`data object` 서브클래스를 조합해 씁니다.

> **닫힌 집합(closed set)이라는 말** — 원전에서는 위상수학의 "경계점을 모두 포함하는 집합"에 빗대지만, 실무에서는 그냥 **"가능한 타입이 미리 다 정해져 있고 밖에서 더 늘릴 수 없는 집합"** 으로 이해하면 충분합니다. 컴파일러가 그 목록을 통째로 알고 있기 때문에 `when` 완전성 검사가 가능한 것입니다.

## 요약 {#summary}

> **TL;DR** — `sealed`는 서브클래스가 같은 모듈·패키지 안에만 존재하도록 제한해, 컴파일러가 **직접 서브클래스 전부를 알게** 만듭니다. 덕분에 `when`에서 모든 경우를 강제(완전성)할 수 있어, 상태가 늘 때 처리 누락을 컴파일 시점에 잡습니다. sealed class는 단일 상속(엄격한 계층), sealed interface는 다중 구현(유연한 조합)에 적합합니다.

1. **닫힌 계층**: 직접 서브클래스는 같은 모듈·패키지에만. 컴파일러가 종류를 전부 안다.
2. **`when` 완전성**: 모든 서브클래스를 다루지 않으면 컴파일 에러. `else` 없이 안전하게 분기하고, 케이스 추가 시 누락을 잡아 준다.
3. **`enum`과의 차이**: 서브클래스마다 다른 프로퍼티를 가질 수 있다(`Success(data)` vs `Error(message)`).
4. **class vs interface**: class는 단일 상속(엄격한 계층), interface(1.5+)는 다중 구현(능력 조합).
5. **`data object`**: 값 없는 상태(`Loading`)를 하나뿐인 인스턴스 + 예쁜 `toString()`으로 표현(1.9+).

<deflist collapsible="true" default-state="collapsed">
<def title="Q) sealed class를 쓰면 무엇이 좋은가요?">

컴파일러가 직접 서브클래스 전부를 알기 때문에 `when` 표현식에서 **완전성(exhaustiveness) 검사**가 가능합니다. 모든 경우를 처리하지 않으면 컴파일이 되지 않고, `else` 가지 없이도 안전하게 분기할 수 있습니다. 특히 나중에 서브클래스(상태)를 추가하면 기존 `when`이 컴파일 에러를 내며 처리 누락을 알려 주므로, 상태가 늘어나는 코드를 안전하게 유지할 수 있습니다.

</def>
<def title="Q) sealed class와 enum class는 어떻게 다른가요?">

`enum`은 정해진 상수 집합을 표현하지만 각 값은 같은 형태를 가집니다. 반면 sealed class의 서브클래스는 **저마다 다른 프로퍼티**를 가질 수 있습니다. 예를 들어 `Success`는 데이터를, `Error`는 에러 메시지를 담을 수 있죠. "경우의 수도 유한하고, 경우마다 담는 데이터도 다른" 상태를 모델링할 때는 sealed가 적합합니다.

</def>
<def title="Q) sealed class와 sealed interface의 차이는 무엇인가요?">

가장 큰 차이는 상속 방식입니다. sealed class의 서브클래스는 클래스를 상속하므로 **단일 상속**만 가능해 엄격한 하나의 계층을 표현합니다. sealed interface(Kotlin 1.5+)는 인터페이스라서 한 클래스가 **여러 sealed interface를 동시에 구현**할 수 있어, 독립적인 능력·역할을 조합할 때 유연합니다. 둘 다 `when` 완전성 검사의 이점은 동일하게 가집니다.

</def>
<def title="Q) sealed의 서브클래스는 어디에 선언해야 하나요?">

직접 서브클래스는 sealed 타입과 **같은 모듈, 같은 패키지** 안에 있어야 합니다. 과거(1.1)에는 같은 파일 안에만 허용됐지만, Kotlin 1.5부터 같은 모듈·패키지라면 여러 파일에 나눠 선언할 수 있게 완화됐습니다. 이 제약 덕분에 컴파일러가 서브클래스 집합 전체를 컴파일 시점에 확정할 수 있습니다.

</def>
</deflist>
