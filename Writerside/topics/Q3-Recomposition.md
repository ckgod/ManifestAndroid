# Q3) Recomposition

## Recomposition은 무엇이고 언제 발생하나요? {#what-is-recomposition}

Compose는 Composition · Layout · Drawing 세 단계를 거쳐 한 번 그려진 UI를, 상태가 바뀌면 다시 그려야 할 때가 있습니다. 이를 위해 도입된 메커니즘이 **리컴포지션(Recomposition)** 입니다. 리컴포지션이 일어나면 흐름은 다시 **Composition 단계** 에서 시작되고, 컴포저블 노드들은 어떤 부분이 바뀌었는지를 프레임워크에 알리며 갱신된 상태가 화면에 반영됩니다.

### 리컴포지션을 트리거하는 조건 {#when-recomposition-occurs}

대부분의 모바일 앱은 데이터 모델의 인-메모리 표현인 **상태(state)** 를 가지고 있고, UI를 이 상태와 동기화하는 일이 핵심 과제입니다. Compose는 두 가지 주요 메커니즘으로 이 동기화를 자동화합니다.

1. **입력 파라미터 변경**: 컴포저블 함수에 전달되는 입력 파라미터가 바뀌면 리컴포지션이 트리거됩니다. Compose 런타임은 새 인자와 이전 인자를 `equals()` 로 비교해, 결과가 `false` 이면 변경이 있다고 판단하고 영향을 받는 UI를 다시 계산합니다.
2. **상태 관찰**: Compose는 자체 **State API** 와 보통 `remember` 의 조합으로 상태 변화를 추적합니다. 컴포저블이 Composition 중에 읽은 `State` 객체를 런타임이 기록해 두었다가, 그 값이 바뀌면 **그 값을 읽은 컴포저블만** 리컴포지션 대상으로 표시(invalidate)합니다. 상태 객체는 메모리에 보존되었다가 리컴포지션 시점에 그대로 복원되므로, 별도의 수동 갱신 없이도 UI가 항상 최신 상태를 반영합니다.

### 리컴포지션 범위 — 전체가 아니라 Scope 단위로 다시 그립니다 {#recomposition-scope}

리컴포지션은 화면 전체를 다시 그리는 작업이 아닙니다. 상태가 바뀌면 Compose는 그 상태를 **읽은 지점을 감싸는 가장 가까운 재시작 가능 범위(restartable scope)** 만 다시 실행합니다. 일반적인 `@Composable` 함수 하나하나가 이 scope가 되며, 따라서 상태 읽기를 어디서 하느냐가 곧 무효화 범위를 결정합니다.

```kotlin
@Composable
fun SearchScreen(viewModel: SearchViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Column {
        // uiState.query를 여기서 읽으면 SearchScreen scope가 무효화 대상이 됩니다.
        SearchTextField(query = uiState.query)   // query 변경 시 이 함수만 재실행되는 게 이상적
        SearchResultList(items = uiState.items)  // query만 바뀌면 skip 가능
    }
}
```
{title="RecompositionScope.kt"}

여기서 주의할 점이 하나 있습니다. `Column`, `Row`, `Box` 같은 레이아웃 컴포저블은 **inline 함수**라서 자체 scope를 만들지 않습니다. 이들 내부에서 상태를 읽으면 무효화는 inline 함수가 아니라 **그 바깥의 호출자 scope** 로 올라갑니다. "Column 안에서만 읽었는데 화면의 다른 형제 컴포저블까지 다시 그려지는" 현상은 대부분 이 때문입니다. 상태 읽기를 가능한 한 **그 값을 실제로 쓰는 말단 컴포저블 안으로** 내리는 것(defer reads)이 무효화 범위를 좁히는 기본 전략입니다.

### Skipping — 리컴포지션을 건너뛰는 조건 {#skipping-and-stability}

scope가 무효화되어 재실행되더라도, 그 안에서 호출되는 자식 컴포저블이 전부 다시 실행되는 것은 아닙니다. Compose 컴파일러는 컴포저블이 **skippable** 하면 호출 지점에 비교 코드를 심어 두고, **모든 파라미터가 이전과 같다고 판단되면 호출 자체를 건너뜁니다(skip)**. 이것이 스마트 리컴포지션이며, 건너뛸 수 있으려면 두 조건이 필요합니다.

1. 파라미터 타입이 **stable** 해야 합니다 — 컴파일러가 "equals가 같으면 정말 같다"고 신뢰할 수 있는 타입.
2. 런타임 비교(`equals()`) 결과가 이전 값과 같아야 합니다.

`List`, `Set` 같은 표준 컬렉션 인터페이스나 다른 모듈에서 온 클래스는 컴파일러가 불변성을 증명할 수 없어 **unstable** 로 분류되고, 그 파라미터를 받는 컴포저블은 값이 같아도 매번 다시 실행됩니다. stable/unstable 판정 규칙과 `@Stable`/`@Immutable` 어노테이션은 [Q5) Stability](Q5-Stability.md)와 [Details: Smart Recomposition](Details-Smart-Recomposition.md)에서, 실전 최적화 기법은 [Q6) Stability 최적화](Q6-Compose-Stability-Optimization.md)에서 깊게 다룹니다.

### 불필요한 리컴포지션을 만드는 흔한 패턴과 해결책 {#common-causes}

실무 코드에서 불필요한 리컴포지션은 대부분 아래 패턴에서 나옵니다.

| 유발 패턴 | 왜 문제인가 | 해결책 |
|--|--|--|
| `List<T>` 파라미터 | 인터페이스라 불변성 증명 불가 → unstable → skip 불가 | `kotlinx.collections.immutable` 의 `ImmutableList`, 또는 `@Immutable` 래퍼 클래스 |
| 다른 모듈/외부 라이브러리 모델 | 컴파일러가 분석 못 해 unstable 처리 | `@Immutable` UI 모델로 매핑, stability configuration file, strong skipping 모드 |
| 인스턴스가 매번 새로 만들어지는 람다 | 외부 변수를 캡처한 람다는 리컴포지션마다 새 객체 → 자식 입장에선 파라미터 변경 | 메서드 참조(`viewModel::onClick`) 사용, `remember(key)` 로 람다 보존 |
| 빠르게 바뀌는 상태(스크롤 오프셋 등)를 그대로 읽기 | 매 프레임 Composition 무효화 | [`derivedStateOf`](Q19-derivedStateOf.md) 로 관심 있는 파생값만 관찰, 또는 lambda 기반 `Modifier`(`graphicsLayer { }`, `offset { }`)로 읽기를 Layout/Drawing 단계로 미루기 |
| 거대한 단일 UiState를 화면 전체에 전달 | 한 필드 변화에 모든 자식의 파라미터가 "바뀐 것처럼" 보임 | 상태를 화면 영역 단위로 분리, 말단에서 필요한 필드만 읽도록 호이스팅 구조 조정 |

```kotlin
// 나쁜 예: firstVisibleItemIndex를 Composition에서 직접 읽음 → 스크롤 매 프레임 리컴포지션
val showButton = listState.firstVisibleItemIndex > 0

// 좋은 예: 경계(0 ↔ 그 외)를 넘을 때만 리컴포지션
val showButton by remember {
    derivedStateOf { listState.firstVisibleItemIndex > 0 }
}
```
{title="DeferredStateRead.kt"}

### 리컴포지션 진단하기 {#tracing-recomposition}

최적화는 측정에서 시작합니다. 어떤 컴포저블이 얼마나 자주 다시 그려지는지를 추적하는 도구는 세 가지를 조합해 사용합니다.

1. **[Layout Inspector](https://developer.android.com/studio/debug/layout-inspector)** — 가장 빠른 진입점입니다. 실행 중인 앱의 Compose 레이아웃을 들여다보며 각 컴포저블의 **리컴포지션 카운트와 skip 카운트** 를 확인할 수 있고, 리컴포지션이 발생하는 순간 해당 영역을 강조 표시해 주므로 핫스팟이 한눈에 드러납니다. 코드 실수로 리컴포지션이 폭주하는 경우뿐 아니라, 반대로 일어나야 할 리컴포지션이 막혀 화면이 갱신되지 않는 문제도 시각적으로 추적할 수 있습니다.
2. **[Composition tracing](https://developer.android.com/develop/ui/compose/tooling/tracing)** — 더 정밀한 진단이 필요할 때 사용합니다. 오버헤드가 작은 시스템 트레이싱으로 일상적인 측정을 하고, 함수 호출 단위까지 들여다봐야 할 때는 메서드 트레이싱을 씁니다.
3. **Compose Compiler 리포트(메트릭)** — 빌드 시점에 각 컴포저블이 `restartable`/`skippable` 인지, 어떤 파라미터가 unstable로 분류됐는지를 리포트로 뽑아 줍니다. Layout Inspector가 "어디가 자주 그려지는지"를 알려준다면, 컴파일러 리포트는 "왜 skip이 안 되는지"의 원인을 알려줍니다.

### 요약 {#summary}

<tldr>

리컴포지션은 Compose의 반응형 UI를 만들어 주는 핵심 메커니즘이지만, 매번 Compose 단계가 다시 실행되는 만큼 성능 비용이 따라옵니다. 입력 파라미터 변화와 State 관찰이 리컴포지션을 트리거하며, 무효화는 화면 전체가 아니라 상태를 읽은 **가장 가까운 restartable scope** 단위로 일어납니다. 파라미터가 모두 stable하고 값이 같으면 호출이 skip되므로, 불안정한 컬렉션·매번 새로 만들어지는 람다·빠르게 바뀌는 상태의 직접 읽기 같은 패턴을 제거하는 것이 최적화의 핵심입니다. Layout Inspector·Composition tracing·컴파일러 리포트로 측정한 뒤 고치는 순서를 지키는 것이 좋습니다.

</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 불필요한 리컴포지션을 줄여 앱 성능을 최적화한 경험이 있다면, 어떤 전략을 사용하셨나요?">

가장 먼저 손대는 부분은 **무엇이 어떻게 자주 리컴포즈되는지를 측정하는 일** 입니다. 감으로 최적화에 들어가면 거의 항상 엉뚱한 곳을 고치게 됩니다. Layout Inspector의 리컴포지션 카운트를 켜 두고 화면을 조작해 보면, 의외로 작은 위젯 하나가 매 프레임 다시 그려지는 식의 핫스팟이 드러납니다. 그 다음에는 Compose Compiler 리포트를 통해 컴포저블 함수가 `restartable`/`skippable` 인지, 어떤 파라미터가 unstable로 분류됐는지를 확인합니다.

이 정보가 모이면 보통 두 갈래의 수정으로 정리됩니다. 첫째는 **상태를 더 작게 쪼개는 것** 입니다. 큰 ViewModel 상태 한 덩어리를 그대로 화면 전체에 흘려보내면 한 필드 변화에 모든 자식이 리컴포즈됩니다. 화면 단위 상태 객체를 잘게 분리하거나, `derivedStateOf` 로 정말 필요한 파생값만 관찰하도록 만들면 영향 범위가 크게 줄어듭니다. 둘째는 **stability를 회복시키는 작업** 입니다. `List<...>` 같은 unstable 컬렉션은 `kotlinx.collections.immutable` 의 `ImmutableList` 로 바꾸거나, 외부 모델은 `@Immutable` 래퍼로 감싸서 컴파일러가 안전하게 skip 할 수 있도록 만듭니다.

마지막으로 람다 캡처도 빼놓을 수 없는 포인트입니다. 클릭 핸들러 같은 람다가 매번 새 인스턴스로 만들어지면 자식 컴포저블 입장에서는 파라미터가 바뀐 것처럼 보여 리컴포지션이 일어납니다. 외부 변수를 캡처하지 않는 단순 람다는 컴파일러가 싱글톤으로 최적화해 주지만, 캡처가 필요한 경우에는 `remember(key)` 로 묶거나 ViewModel 함수 참조 형태로 끌어올리는 식으로 동일성을 유지합니다. 이렇게 측정 → 상태 분리 → 안정성 회복 → 람다 안정화 순서로 접근하면, 대부분의 화면에서 의미 있는 성능 향상을 얻을 수 있습니다.

</def>
<def title="Q) 상태가 하나 바뀌면 화면 전체가 다시 그려지나요? 리컴포지션의 범위는 어떻게 결정되나요?">

아닙니다. Compose는 상태를 **읽은 지점을 감싸는 가장 가까운 restartable scope** 만 무효화합니다. 일반적인 `@Composable` 함수가 그 단위이므로, 같은 상태라도 어느 함수 안에서 읽느냐에 따라 다시 실행되는 범위가 달라집니다. 그래서 상태 읽기를 실제로 그 값을 쓰는 말단 컴포저블로 내리는 것만으로도 무효화 범위를 크게 줄일 수 있습니다.

한 가지 함정은 `Column` · `Row` · `Box` 가 inline 함수라 자체 scope를 만들지 않는다는 점입니다. 이들 내부에서 상태를 읽으면 무효화가 호출자 scope로 올라가서, 형제 컴포저블까지 함께 재실행되는 것처럼 보입니다. 또한 scope가 재실행되더라도 자식 컴포저블의 파라미터가 모두 stable하고 값이 같으면 해당 호출은 skip되기 때문에, 실제 재실행 범위는 "무효화된 scope 중 파라미터가 실제로 바뀐 부분"으로 좁혀집니다.

</def>
<def title="Q) 스크롤 위치처럼 매 프레임 바뀌는 상태 때문에 리컴포지션이 폭주한다면 어떻게 해결하시겠어요?">

두 가지 접근을 상황에 따라 씁니다. 첫째, 연속적인 값에서 **관심 있는 불리언/구간 파생값만 관찰** 하도록 `derivedStateOf` 를 사용합니다. 예를 들어 `firstVisibleItemIndex > 0` 처럼 경계를 넘는 순간에만 값이 바뀌도록 만들면, 스크롤 매 프레임이 아니라 경계 통과 시에만 리컴포지션이 일어납니다.

둘째, 값이 정말 매 프레임 UI에 반영되어야 한다면(패럴랙스 오프셋 등) 리컴포지션 자체를 피하고 **상태 읽기를 Layout/Drawing 단계로 미룹니다**. `Modifier.offset { }`, `Modifier.graphicsLayer { }` 같은 람다 기반 Modifier는 람다가 Composition이 아닌 이후 단계에서 실행되므로, 값이 바뀌어도 Composition 단계를 건너뛰고 배치·그리기만 갱신됩니다. 정리하면 "빈도를 줄일 수 있으면 derivedStateOf, 빈도를 줄일 수 없으면 읽기를 뒤 단계로 미루기"가 원칙입니다.

</def>
</deflist>
