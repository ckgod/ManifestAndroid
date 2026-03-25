# Q3) Recomposition

## Recomposition은 무엇이고 언제 발생하나요? {#what-is-recomposition}

Compose는 Composition · Layout · Drawing 세 단계를 거쳐 한 번 그려진 UI를, 상태가 바뀌면 다시 그려야 할 때가 있습니다. 이를 위해 도입된 메커니즘이 **리컴포지션(Recomposition)** 입니다. 리컴포지션이 일어나면 흐름은 다시 **Composition 단계** 에서 시작되고, 컴포저블 노드들은 어떤 부분이 바뀌었는지를 프레임워크에 알리며 갱신된 상태가 화면에 반영됩니다.

### 리컴포지션을 트리거하는 조건 {#when-recomposition-occurs}

대부분의 모바일 앱은 데이터 모델의 인-메모리 표현인 **상태(state)** 를 가지고 있고, UI를 이 상태와 동기화하는 일이 핵심 과제입니다. Compose는 두 가지 주요 메커니즘으로 이 동기화를 자동화합니다.

1. **입력 파라미터 변경**: 컴포저블 함수에 전달되는 입력 파라미터가 바뀌면 리컴포지션이 트리거됩니다. Compose 런타임은 새 인자와 이전 인자를 `equals()` 로 비교해, 결과가 `false` 이면 변경이 있다고 판단하고 영향을 받는 UI를 다시 계산합니다.
2. **상태 관찰**: Compose는 자체 **State API** 와 보통 `remember` 의 조합으로 상태 변화를 추적합니다. 이 방식은 상태 객체를 메모리에 보존했다가 리컴포지션 시점에 그대로 복원해 주므로, 별도의 수동 갱신 없이도 UI가 항상 최신 상태를 반영하게 됩니다.

### 리컴포지션과 성능의 관계 {#recomposition-and-performance}

리컴포지션은 Compose의 반응형 본질을 만들어 주는 핵심이지만, 과도하거나 불필요한 리컴포지션은 성능을 떨어뜨립니다. 어떤 컴포저블이 얼마나 자주 다시 그려지는지를 추적하고 그 원인을 진단하는 것은 Compose 앱 성능 최적화의 가장 기본적인 작업입니다. 리컴포지션 빈도는 stability(안정성) 같은 요인에 영향을 받으며, 자세한 내용은 별도 토픽에서 다룹니다.

리컴포지션 카운트를 직접 들여다보고 싶다면 [Layout Inspector](https://developer.android.com/studio/debug/layout-inspector)가 가장 빠른 도구입니다. 에뮬레이터나 실제 디바이스에서 실행 중인 앱의 Compose 레이아웃을 들여다보며, 각 컴포저블이 몇 번 리컴포즈되었는지, 또는 몇 번 건너뛰어졌는지를 확인할 수 있습니다. 코드 실수로 인해 리컴포지션이 폭주하거나, 반대로 일어나야 할 리컴포지션이 막혀 화면이 갱신되지 않는 문제를 시각적으로 추적할 수 있습니다.

Android Studio의 Layout Inspector는 리컴포지션이 발생하는 순간 해당 영역을 강조 표시해 주기 때문에, UI 어느 부분이 자주 다시 그려지는지를 한눈에 파악할 수 있습니다. 좀 더 정밀한 진단이 필요하다면 [Composition tracing](https://developer.android.com/develop/ui/compose/tooling/tracing)을 함께 활용할 수 있습니다. 시스템 트레이싱은 오버헤드가 작아 일상적인 측정에, 메서드 트레이싱은 함수 호출 단위까지 들여다봐야 할 때 유용합니다.

### 요약 {#summary}

<tldr>
리컴포지션은 Compose의 반응형 UI를 만들어 주는 핵심 메커니즘이지만, 매번 Compose 단계가 다시 실행되는 만큼 성능 비용이 따라옵니다. 입력 파라미터 변화와 State 관찰이 리컴포지션을 트리거하며, Layout Inspector나 Composition tracing 같은 도구로 빈도를 추적해 불필요한 리컴포지션을 줄이는 것이 최적화의 출발점입니다. 더 깊은 가이드는 *6 Jetpack Compose Guidelines to Optimize Your App Performance*, *Optimize App Performance By Mastering Stability in Jetpack Compose* 같은 자료를 참고할 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) 불필요한 리컴포지션을 줄여 앱 성능을 최적화한 경험이 있다면, 어떤 전략을 사용하셨나요?">

가장 먼저 손대는 부분은 **무엇이 어떻게 자주 리컴포즈되는지를 측정하는 일** 입니다. 감으로 최적화에 들어가면 거의 항상 엉뚱한 곳을 고치게 됩니다. Layout Inspector의 리컴포지션 카운트를 켜 두고 화면을 조작해 보면, 의외로 작은 위젯 하나가 매 프레임 다시 그려지는 식의 핫스팟이 드러납니다. 그 다음에는 Compose Compiler 리포트를 통해 컴포저블 함수가 `restartable`/`skippable` 인지, 어떤 파라미터가 unstable로 분류됐는지를 확인합니다.

이 정보가 모이면 보통 두 갈래의 수정으로 정리됩니다. 첫째는 **상태를 더 작게 쪼개는 것** 입니다. 큰 ViewModel 상태 한 덩어리를 그대로 화면 전체에 흘려보내면 한 필드 변화에 모든 자식이 리컴포즈됩니다. 화면 단위 상태 객체를 잘게 분리하거나, `derivedStateOf` 로 정말 필요한 파생값만 관찰하도록 만들면 영향 범위가 크게 줄어듭니다. 둘째는 **stability를 회복시키는 작업** 입니다. `List<...>` 같은 unstable 컬렉션은 `kotlinx.collections.immutable` 의 `ImmutableList` 로 바꾸거나, 외부 모델은 `@Immutable` 래퍼로 감싸서 컴파일러가 안전하게 skip 할 수 있도록 만듭니다.

마지막으로 람다 캡처도 빼놓을 수 없는 포인트입니다. 클릭 핸들러 같은 람다가 매번 새 인스턴스로 만들어지면 자식 컴포저블 입장에서는 파라미터가 바뀐 것처럼 보여 리컴포지션이 일어납니다. 외부 변수를 캡처하지 않는 단순 람다는 컴파일러가 싱글톤으로 최적화해 주지만, 캡처가 필요한 경우에는 `remember(key)` 로 묶거나 ViewModel 함수 참조 형태로 끌어올리는 식으로 동일성을 유지합니다. 이렇게 측정 → 상태 분리 → 안정성 회복 → 람다 안정화 순서로 접근하면, 대부분의 화면에서 의미 있는 성능 향상을 얻을 수 있습니다.

</def>
</deflist>
