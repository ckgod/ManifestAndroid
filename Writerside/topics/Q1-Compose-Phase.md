# Q1) Compose의 렌더링 단계

## Compose의 렌더링 단계는 무엇인가요? {#compose-phases}

Jetpack Compose는 **Composition**, **Layout**, **Drawing** 세 단계로 나뉘는 명확한 렌더링 파이프라인을 따릅니다. 이 세 단계는 순차적으로 실행되어 UI를 구성하고, 배치하고, 화면에 그려내는 역할을 각각 담당합니다.

![compose-phase.png](compose-phase.png)

### Composition (컴포지션) {#composition-phase}

Composition 단계는 `@Composable` 함수를 실행하여 UI 트리를 구성하는 단계입니다. Compose는 이 단계에서 초기 UI 구조를 빌드하고, 슬롯 테이블(Slot Table)이라는 자료구조에 Composable 간의 관계를 기록합니다. 이후 상태 변화가 발생하면 Composition 단계가 영향을 받는 UI 부분만 재계산하여 리컴포지션을 트리거합니다.

![composition.png](composition.png)

주요 작업:
- `@Composable` 함수 실행
- UI 트리 생성 및 업데이트
- 리컴포지션을 위한 변경 사항 추적

### Layout (레이아웃) {#layout-phase}

Layout 단계는 Composition 단계 이후에 실행됩니다. 제공된 제약 조건(constraints)을 기반으로 각 UI 요소의 크기와 위치를 결정합니다. 각 Composable은 자신의 자식 요소를 측정하고, 자신의 크기를 결정한 뒤, 부모 컨테이너 내에서의 위치를 정의합니다.

![layout.png](layout.png)

주요 작업:
- UI 컴포넌트 측정
- 너비, 높이, 위치 결정
- 부모 컨테이너 내에서 자식 요소 배치

### Drawing (드로잉) {#drawing-phase}

Drawing 단계는 Composition과 Layout 단계에서 결정된 UI 요소를 화면에 실제로 렌더링하는 단계입니다. Compose는 이 과정에서 Skia 그래픽 엔진을 사용하여 부드럽고 하드웨어 가속된 렌더링을 보장합니다. 커스텀 드로잉 로직은 Compose의 `Canvas` API를 통해 구현할 수 있습니다.

![drawing.png](drawing.png)

주요 작업:
- 시각적 요소 렌더링
- UI 컴포넌트를 화면에 그리기
- 커스텀 드로잉 연산 적용

### 요약 {#summary}

<tldr>
Jetpack Compose의 렌더링은 세 단계로 구성됩니다. **Composition**은 `@Composable` 함수를 실행하여 UI 트리를 구성하고, **Layout**은 각 컴포넌트의 크기와 위치를 결정하며, **Drawing**은 Skia 엔진을 통해 UI를 화면에 그립니다. 이 파이프라인은 순차적으로 실행되어 효율적이고 확장 가능한 UI 렌더링을 가능하게 합니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Composition 단계에서는 어떤 일이 발생하며, 리컴포지션과 어떤 관계가 있나요?">

Composition 단계에서는 `@Composable` 함수들이 실행되어 현재 상태를 기반으로 UI 트리가 생성됩니다. Compose는 이 트리를 슬롯 테이블(Slot Table)에 저장하여 각 Composable의 상태와 관계를 추적합니다.

상태(State)가 변경되면 Compose는 해당 상태를 읽는 `@Composable` 함수만 선택적으로 재실행합니다. 이를 **리컴포지션**이라 하며, 전체 UI 트리를 처음부터 다시 구성하는 대신 변경된 부분만 효율적으로 갱신합니다. 이로써 불필요한 재렌더링 비용을 최소화하여 앱 성능을 유지합니다.

</def>
<def title="Q) Layout 단계는 어떻게 동작하나요?">

Layout 단계는 제약 조건(constraints) 기반의 단방향 측정 방식으로 동작합니다.

1. **제약 전달**: 부모 Composable이 자식에게 최소/최대 너비와 높이 제약을 전달합니다.
2. **자식 측정**: 각 Composable은 자신의 자식을 측정하여 크기를 파악합니다. Compose의 레이아웃 시스템은 각 노드를 **한 번만** 측정하도록 설계되어 있어(단일 측정 패스), 깊은 계층 구조에서도 성능을 유지합니다.
3. **크기 결정 및 배치**: 자식 크기 정보를 바탕으로 자신의 크기를 결정하고, 자식들의 위치(x, y 좌표)를 정의합니다.

이 과정은 UI 트리의 루트부터 리프 노드까지 재귀적으로 진행됩니다.

</def>
</deflist>
