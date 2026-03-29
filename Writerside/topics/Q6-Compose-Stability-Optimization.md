# Q6) Stability 개선을 통한 Compose 성능 최적화

## Stability 개선으로 Compose 성능을 최적화한 경험이 있나요? {#optimizing-by-stability}

Jetpack Compose의 성능 최적화는 결국 컴포저블 함수를 **안정화(stability)** 하고 불필요한 리컴포지션을 줄이는 일에 수렴합니다. stability 가 보장될수록 Compose는 어느 함수를 리컴포지션에서 건너뛸지를 더 정확하게 판단할 수 있습니다. 다음은 stability 를 확보하면서 컴파일러의 고급 기능까지 활용해 성능을 개선하는 핵심 전략들입니다.

### 불변(Immutable) 컬렉션 활용 {#immutable-collections}

`List` 나 `Map` 같은 읽기 전용 컬렉션은 Compose 컴파일러 입장에서 unstable 로 분류됩니다. 내부 구현이 가변일 가능성을 배제할 수 없기 때문입니다. 다음 예시를 봅시다.

```kotlin
internal var mutableUserList: MutableList<User> = mutableListOf()
public val userList: List<User> = mutableUserList
```
{title="MutableListExample.kt"}

`userList` 는 `List` 로 선언되어 읽기 전용처럼 보이지만, 실제 구현체는 `MutableList` 입니다. 컴파일 시점에는 이 컬렉션이 정말 불변인지 알 수 없으므로, 컴파일러는 안전한 쪽으로 이런 인스턴스를 unstable 로 취급해 리컴포지션 정합성을 유지합니다.

stability 를 확보하려면 [kotlinx.collections.immutable](https://github.com/Kotlin/kotlinx.collections.immutable)이나 [Guava의 immutable 컬렉션](https://github.com/google/guava/wiki/ImmutableCollectionsExplained) 같은 본질적으로 안정적인 라이브러리를 사용할 수 있습니다. `ImmutableList`, `ImmutableSet` 같은 타입을 사용하면 컬렉션이 읽기 전용이며 효율적인 리컴포지션에 적합하다는 사실을 컴파일러가 신뢰하게 됩니다.

> **참고**: 컴파일러가 어떤 컬렉션을 stable 로 취급하는지를 더 자세히 보고 싶다면 Compose 컴파일러 라이브러리의 [KnownStableConstructs.kt](https://github.com/JetBrains/kotlin/blob/eadcce82e781d7be850118e82333893ab7cf10a9/plugins/compose/compiler-hosted/src/main/java/androidx/compose/compiler/plugins/kotlin/analysis/KnownStableConstructs.kt#L48) 파일을 참고하면 좋습니다. stable 로 취급해야 하는 클래스들의 패키지 이름이 명시적으로 나열되어 있습니다.

### 람다 안정성 {#lambda-stability}

Compose는 람다 표현식을 외부 변수 캡처 여부에 따라 다르게 다룹니다.

- **비캡처 람다(Non-Capturing Lambdas)**: 외부 변수를 캡처하지 않는 람다는 stable 로 취급되며, 싱글톤으로 최적화되어 불필요한 할당을 만들지 않습니다.
- **캡처 람다(Capturing Lambdas)**: 외부 변수를 참조하는 람다는 변경에 동적으로 반응할 수 있도록 `remember` 로 메모이즈됩니다. 변화의 기준이 되는 외부 변수를 `remember` 의 key 파라미터로 전달함으로써, 리컴포지션을 가로질러 일관성과 안정성을 유지합니다.

캡처라는 말은 람다가 자신을 둘러싼 스코프의 변수에 의존하고 있다는 뜻입니다. 외부 변수에 의존하지 않는 람다는 비캡처 람다이며, 다음 예시처럼 보입니다.

```kotlin
modifier.clickable {
    Log.d("Log", "This Lambda doesn't capture any values")
}
```
{title="NonCapturingLambda.kt"}

비캡처 람다는 Kotlin이 싱글톤으로 최적화하여 불필요한 할당이 사라집니다. 반대로 외부 변수를 참조하는 람다는 캡처 람다입니다.

```kotlin
var sum = 0
ints.filter { it > 0 }.forEach {
    sum += it
}
```
{title="CapturingLambda.kt"}

### 래퍼 클래스(Wrapper Classes) {#wrapper-classes}

직접 통제할 수 없는 unstable 클래스(예: 외부 라이브러리에서 제공되는 타입)는 stability 어노테이션을 적용한 래퍼 클래스를 만들어 우회할 수 있습니다.

```kotlin
@Immutable
data class ImmutableUserList(
    val user: List<User>
)
```
{title="WrapperClasses.kt"}

이 래퍼 클래스를 컴포저블 함수의 파라미터 타입으로 사용하면 됩니다.

```kotlin
@Composable
fun UserAvatars(
    modifier: Modifier,
    userList: ImmutableUserList,
)
```
{title="WrapperClassesUsage.kt"}

### Stability Configuration File {#stability-config-file}

Compose Compiler 1.5.5부터는 [stability 설정 파일](https://developer.android.com/develop/ui/compose/performance/stability/fix#configuration-file)에 stable 로 취급해야 할 클래스를 직접 명시할 수 있습니다.

- 프로젝트 루트에 `compose_compiler_config.conf` 파일을 만들고 stable 로 취급할 클래스들을 나열합니다.
- `build.gradle.kts` 에서 이 설정 파일을 사용하도록 구성하면, Compose 컴파일러가 해당 클래스들의 리컴포지션을 스킵 후보로 인식합니다.
- 외부 라이브러리 클래스나 커스텀 타입을 안정화하는 데 특히 유용합니다. 이 기능을 활용하면 프로젝트 전반에 걸쳐 특정 클래스를 stable 로 지정할 수 있어, 매번 래퍼 클래스를 만드는 수고를 덜 수 있습니다.

### Strong Skipping Mode {#strong-skipping-mode}

Compose Compiler 1.5.4에서 실험적으로 도입된 [Strong Skipping Mode](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping)는 restartable 컴포저블 함수에 대해 unstable 파라미터가 포함되어 있더라도 리컴포지션을 건너뛸 수 있도록 해 줍니다.

- stable 파라미터는 객체 동등성(equality)으로, unstable 파라미터는 인스턴스 동일성(instance equality)으로 비교합니다.
- 특정 함수를 이 동작에서 제외하고 싶다면 `@NonSkippableComposable` 어노테이션을 사용할 수 있습니다.

### 요약 {#summary}

<tldr>
파라미터를 안정화하고, 불변 컬렉션을 사용하고, 람다 캡처를 정리하고, 래퍼 클래스나 stability 설정 파일을 활용하고, Strong Skipping Mode 같은 고급 기능을 함께 동원하면 Jetpack Compose 앱의 성능을 의미 있는 수준으로 끌어올릴 수 있습니다. 이 전략들은 불필요한 리컴포지션을 줄이고 UI 반응성을 높여 매끄러운 사용자 경험을 만들어 줍니다. 더 깊은 자료는 *Optimize App Performance by Mastering Stability in Jetpack Compose* 와 GitHub의 *compose-performance* 저장소를 참고할 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) List 를 파라미터로 받는 컴포저블 함수가 불필요한 리컴포지션을 일으킨다면 어떻게 최적화하시겠습니까?">

가장 먼저 점검할 부분은 **컬렉션 자체가 stable 로 인식되고 있는가** 입니다. 표준 `List` 인터페이스는 구현체가 가변일 수 있으므로 Compose 컴파일러가 unstable 로 분류하고, 그 결과 컴포저블이 매번 리컴포지션 후보가 됩니다. 이 자리에서 일반적으로 가장 적은 비용으로 큰 효과를 보는 변경은 `kotlinx.collections.immutable` 의 `ImmutableList` 로 타입을 바꾸는 것입니다. 이렇게 하면 컴파일러가 컬렉션을 stable 로 인식해 동일 인스턴스가 다시 들어왔을 때 컴포저블을 건너뛸 수 있습니다.

`ImmutableList` 도입이 어렵다면 stability 설정 파일이나 래퍼 클래스가 차선책이 됩니다. 예를 들어 `@Immutable data class WrappedList(val items: List<Item>)` 같은 래퍼를 만들고 컴포저블에서는 이 래퍼 타입을 파라미터로 받는 식입니다. 실제로 컬렉션의 내용이 같은 한 같은 래퍼 인스턴스를 그대로 흘려보내면 리컴포지션이 안전하게 스킵됩니다. 외부 모델을 그대로 쓸 수밖에 없는 경우에는 `compose_compiler_config.conf` 에 해당 클래스를 stable 로 등록해 동일한 효과를 얻을 수 있습니다.

여기서 한 단계 더 나아가려면 Compose Compiler 리포트로 실제 분류 결과를 확인하는 것이 좋습니다. "왜 unstable 인가" 가 적힌 리포트를 보면 List 자체가 문제인 경우와, 그 안의 요소 타입이 문제인 경우가 분명히 갈립니다. 후자라면 List 만 ImmutableList 로 바꾸어도 의미가 없고, 요소 타입까지 stable 하게 정리해야 합니다. 마지막으로 화면이 정말 큰 데이터셋을 다룬다면 Strong Skipping Mode를 켜는 것도 고려할 수 있습니다. 단 이 모드는 동작 모델이 달라지므로, 도입 전에 회귀 테스트와 프로파일링을 함께 수행하는 것이 안전합니다.

</def>
<def title="Q) 리컴포지션 효율을 높이기 위해 어떤 API나 Compose 컴파일러 기능을 활용해 본 적이 있나요?">

먼저 일상적으로 손을 가장 많이 대는 도구는 **Compose Compiler 리포트** 입니다. 빌드 옵션을 켜면 `restartable`/`skippable` 분류와 unstable 파라미터 목록이 모듈별 리포트 파일로 떨어지는데, 이 데이터를 토대로 개선 우선순위를 정합니다. 그다음으로는 **Layout Inspector의 리컴포지션 카운트** 를 켜고 실제 화면에서 어디가 자주 다시 그려지는지를 측정해 리포트와 교차 확인합니다. 이 두 가지가 맞물려야 추측이 아닌 측정 기반 최적화가 가능합니다.

코드 레벨에서는 **`derivedStateOf`** 와 **`remember`** 의 조합을 적극적으로 사용합니다. ViewModel 의 큰 상태 객체에서 일부만 파생해 컴포저블에 전달할 때, `derivedStateOf` 로 정말 변한 경우에만 리컴포지션이 일어나도록 묶어 둡니다. 람다 캡처가 잦은 화면에서는 클릭 핸들러나 콜백을 ViewModel 메서드 참조로 끌어올리거나 `remember(key)` 로 묶어 같은 인스턴스를 유지합니다. 컬렉션 파라미터에는 앞서 이야기한 `ImmutableList` 와 `@Immutable` 래퍼를 도입해 stability 를 회복시키고, 외부 라이브러리 모델은 stability 설정 파일에 등록해 두는 식입니다.

마지막 무기로는 **Strong Skipping Mode** 와 **Baseline Profile** 이 있습니다. Strong Skipping Mode는 unstable 파라미터까지 인스턴스 동일성으로 비교하므로 리컴포지션 스킵 빈도를 크게 늘려 줍니다. Baseline Profile은 stability 와 직접적인 관련은 없지만, 자주 호출되는 컴포저블 경로를 미리 컴파일해 두어 리컴포지션 비용 자체를 줄여 주므로 stability 개선과 함께 적용하면 시너지가 큽니다. 이렇게 측정 → 분류 점검 → stability 회복 → 람다·상태 정리 → 컴파일러 옵션의 순서로 접근하는 흐름이 실무에서 가장 효과가 컸습니다.

</def>
</deflist>
