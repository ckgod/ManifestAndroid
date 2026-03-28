# Q5) Stability

## Jetpack Compose의 Stability는 무엇이며 성능과 어떤 관계가 있나요? {#what-is-stability}

Jetpack Compose에서 **stability(안정성)** 는 어떤 클래스나 타입이 시간이 지나도 같은 입력에 대해 일관된 결과를 만들어 내는 성질을 가리킵니다. 안정적이라는 것은 리컴포지션 동안 여러 번 호출되더라도 그 동작이 예측을 벗어나지 않는다는 뜻이며, 이는 Compose가 불필요한 리컴포지션 없이 효율적으로 UI 갱신을 처리하기 위한 핵심 조건입니다.

리컴포지션을 트리거하는 다양한 메커니즘 가운데, 컴포저블 함수에 전달되는 **파라미터의 안정성** 은 특히 중요한 역할을 합니다. Compose Runtime과 컴파일러가 "지금 이 컴포저블을 다시 실행해야 하는가?"를 판단하는 데 직접 사용되기 때문입니다.

Compose 컴파일러는 컴포저블 함수의 파라미터를 분석해 **stable** 또는 **unstable** 로 분류합니다. Compose Runtime은 이 분류 결과를 바탕으로, 입력 변화에 따라 컴포저블을 다시 실행할지 여부를 효율적으로 결정합니다.

### Stable vs Unstable {#stable-vs-unstable}

파라미터가 어떤 기준으로 stable / unstable로 나뉘는지부터 살펴봅시다. 분류는 Compose 컴파일러가 다음과 같은 기준에 따라 수행합니다.

- **원시 타입(Primitive Types)**: `String` 을 포함한 원시 타입은 예기치 않게 변하지 않으므로 본질적으로 stable 합니다.
- **함수 타입(Function Types)**: 외부 값을 캡처하지 않는 람다 표현식은 동작이 예측 가능하므로 stable 합니다.
- **클래스(Classes)**: 불변(immutable)이고 안정적인 public 프로퍼티만 가진 data class는 stable 로 간주됩니다. 또한 `@Stable` 이나 `@Immutable` 같은 안정성 어노테이션이 명시적으로 붙은 클래스도 stable 로 인식됩니다.

예를 들어 다음과 같은 data class를 떠올려 봅시다.

```kotlin
data class User(
    val id: Int,
    val name: String,
)
```
{title="Stable.kt"}

`User` data class는 불변 원시 프로퍼티들로만 구성되어 있어 Compose 컴파일러가 stable 로 분류합니다.

반대로 다음 기준에 해당하면 unstable 로 분류됩니다.

- **인터페이스와 추상 클래스**: `List`, `Map`, `Any` 처럼 컴파일 시점에 구현체가 보장되지 않는 타입은 unstable 로 간주됩니다.
- **가변 프로퍼티를 가진 클래스**: 한 개라도 가변(`var`)이거나 그 자체가 unstable 한 public 프로퍼티가 포함되면 그 클래스도 unstable 로 분류됩니다.

다음 예시를 보겠습니다.

```kotlin
data class MutableUser(
    val id: Int,
    var name: String, // 가변 프로퍼티 때문에 클래스가 unstable해집니다.
)
```
{title="Unstable.kt"}

`MutableUser` 의 프로퍼티는 대부분 원시 타입이지만, `name` 이 `var` 이라는 사실 하나로 클래스 전체가 unstable 로 분류됩니다. 클래스의 안정성은 모든 프로퍼티의 안정성을 종합적으로 평가하기 때문에, 가변 프로퍼티 한 개만으로도 클래스 전체가 흔들릴 수 있습니다.

### Composable 함수의 분류 {#inferring-composable-functions}

Compose 컴파일러는 Kotlin 컴파일러 플러그인으로 동작하며, 빌드 시점에 개발자가 작성한 소스를 분석합니다. 단순히 분석만 하는 것이 아니라, 컴포저블 함수를 효율적으로 실행할 수 있도록 원본 코드를 수정하기도 합니다.

성능 최적화를 위해 컴파일러는 컴포저블 함수를 **Restartable**, **Skippable**, **Moveable**, **Replaceable** 같은 카테고리로 분류합니다. 이 가운데 리컴포지션과 가장 직접 관련 있는 것이 Restartable과 Skippable입니다.

- **Restartable**: 입력이나 상태가 바뀔 때 Compose Runtime이 다시 실행할 수 있는 컴포저블입니다. 대부분의 컴포저블이 기본적으로 restartable 이며, 이 분류는 리컴포지션 흐름의 토대가 됩니다.
- **Skippable**: 특정 조건이 만족되면 리컴포지션을 건너뛸 수 있는 컴포저블입니다. 큰 함수 계층의 루트에서 skip 가능하면, 그 아래로 이어지는 자식 호출 비용을 한꺼번에 절약할 수 있어 영향이 큽니다. 한 함수가 restartable 이면서 동시에 skippable 일 수도 있는데, 이 경우 필요할 때는 다시 실행되고 필요 없을 때는 건너뛰는 식으로 동작합니다.

### 요약 {#summary}

<tldr>
Stability는 Compose의 성능과 신뢰성에 직접 영향을 주는 기초 개념입니다. 컴포저블이 stable 한 타입을 사용하고 부수 효과를 피하도록 설계하면, 리컴포지션이 매끄러워지고 UI 갱신 비용이 최소화됩니다. Compose Runtime의 효율성을 온전히 활용하기 위해서는 stability 원칙을 받아들이는 것이 출발점이 됩니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Compose 컴파일러는 어떤 기준으로 파라미터의 stability 를 결정하며, 그것이 리컴포지션에 왜 중요한가요?">

Compose 컴파일러는 파라미터 타입을 분석해 그 값이 시간이 지나도 일관된 결과를 만들어 낼 수 있는지를 판단합니다. 원시 타입과 `String`, 외부 값을 캡처하지 않는 람다, 그리고 모든 public 프로퍼티가 불변이며 안정적인 data class는 stable 로 분류됩니다. 반대로 인터페이스나 추상 클래스, 가변 프로퍼티가 하나라도 포함된 클래스는 unstable 로 분류됩니다. `@Stable` 이나 `@Immutable` 어노테이션을 붙이면 컴파일러가 자동 추론으로 잡지 못하는 케이스를 명시적으로 stable 로 끌어올릴 수도 있습니다.

이 분류가 리컴포지션 비용을 좌우하는 이유는 Compose 런타임이 "이 파라미터가 정말 바뀌었는가" 를 판단할 때 stability 정보를 단서로 삼기 때문입니다. stable 한 파라미터는 `equals()` 비교 결과를 신뢰할 수 있어 값이 같으면 안전하게 컴포저블을 건너뛸 수 있습니다. 반면 unstable 한 파라미터가 들어오면 런타임은 안전한 쪽으로 결정해 무조건 리컴포지션을 트리거합니다. 결과적으로 unstable 파라미터 하나가 그 컴포저블과 그 아래 자식들의 skip 가능성을 모두 무너뜨릴 수 있습니다.

따라서 stability 는 단순한 코드 스타일 문제가 아니라, 자주 호출되는 컴포저블의 성능을 결정하는 입력값에 가깝습니다. 도메인 모델은 가능한 한 불변 data class로, 컬렉션은 `kotlinx.collections.immutable` 의 immutable 변형으로, 외부 라이브러리 모델처럼 통제할 수 없는 타입은 `@Immutable` 래퍼 또는 stability 설정 파일로 끌어올리는 식의 작업이 곧 리컴포지션 최적화의 핵심이 됩니다.

</def>
<def title="Q) Jetpack Compose의 @Stable 과 @Immutable 어노테이션은 무엇이며, 언제 사용해야 하나요?">

두 어노테이션은 모두 클래스의 stability 를 컴파일러에 명시적으로 알려 주기 위한 도구이며, 그 약속 강도가 다릅니다. `@Immutable` 은 "이 클래스의 public 프로퍼티는 모두 불변이며 한 번 만들어진 인스턴스는 절대 바뀌지 않는다" 는 강한 약속입니다. 컴파일러는 이 약속을 신뢰해 같은 인스턴스가 다시 들어오면 컴포저블 호출을 건너뛸 수 있습니다. 네트워크 응답이나 DB 엔티티에서 만들어진 도메인 모델, 한번 만들어 두고 갱신하지 않는 설정 객체에 자연스럽게 어울립니다.

`@Stable` 은 좀 더 약한 약속에 가깝습니다. "내부에 가변 상태가 있을 수 있지만, 그 변경은 통제되어 있고 같은 값을 다시 넣으면 같은 결과가 나온다" 는 보장입니다. 대표적인 예가 Compose 자체의 `State` 인터페이스입니다. 외부에서는 불변 `value` 프로퍼티만 노출하지만 내부 구현(예: `MutableState`)은 setter 를 통해 값을 갱신합니다. 이런 식으로 가변성을 자기 안에서 통제할 수 있는 인터페이스나 UI 상태 클래스에 `@Stable` 을 붙이면, 컴파일러가 안전하게 stable 로 취급해 줍니다.

언제 사용할지에 대한 직관적인 기준은 다음과 같습니다. **완전 불변** 으로 모델링되는 데이터 클래스(특히 외부에서 받은 결과를 그대로 화면에 흘리는 경우)에는 `@Immutable`, **인터페이스 또는 통제된 가변성을 가진 UI 상태** 처럼 stability 가 분명하지만 컴파일러가 자동으로 잡아내지 못하는 경우에는 `@Stable` 을 붙입니다. 두 어노테이션 모두 잘못 사용하면 컴파일러의 스킵 결정이 틀어져 silent 한 UI 버그를 만들 수 있으므로, "정말로 그 약속이 지켜지는가?" 를 코드 리뷰 시점에 함께 점검하는 습관이 중요합니다.

</def>
</deflist>
