# Details: Smart Recomposition

## Smart Recomposition이란? {#what-is-smart-recomposition}

stability와 Compose 컴파일러가 stable / unstable 타입을 구분하는 방식을 살펴봤다면, 이제 그 분류가 실제로 어떤 식으로 리컴포지션에 영향을 주는지 들여다볼 차례입니다. Compose 컴파일러는 컴포저블 함수에 전달되는 파라미터의 stability 를 평가하고, 그 결과를 Compose Runtime이 효율적인 리컴포지션 관리에 활용합니다.

클래스의 stability 가 결정되면 Compose Runtime은 이 정보를 **smart recomposition** 이라는 메커니즘을 통해 활용합니다. Smart recomposition은 컴파일러가 제공한 안정성 데이터를 기반으로 불필요한 갱신을 선택적으로 건너뛰어, UI 성능과 반응성을 최적화합니다.

### Smart Recomposition의 동작 방식 {#how-it-works}

새로운 입력이 컴포저블 함수에 전달될 때마다 Compose는 그 클래스의 `equals()` 를 사용해 이전 값과 비교합니다.

- **stable 파라미터, 변화 없음**: 파라미터가 stable 하고 값이 바뀌지 않았다면(`equals()` 가 `true`), Compose는 해당 UI 컴포넌트의 리컴포지션을 건너뜁니다.
- **stable 파라미터, 값 변경됨**: stable 한 파라미터의 값이 바뀌었다면(`equals()` 가 `false`), 런타임은 리컴포지션을 트리거해 UI가 갱신된 상태를 반영하도록 합니다.
- **unstable 파라미터**: 파라미터가 unstable 하면 값 변화 여부와 무관하게 항상 리컴포지션이 트리거됩니다.

### 불필요한 리컴포지션을 피하는 일이 왜 중요한가 {#why-it-matters}

중복된 리컴포지션을 줄이면 함수를 다시 실행하고 UI 요소를 다시 그리는 데 드는 계산 비용이 함께 줄어듭니다. 특히 여러 상태에 의존하는 컴포넌트가 깊게 쌓여 있는 복잡한 UI 계층에서는, 불필요한 리컴포지션이 곧바로 프레임 드롭으로 이어질 수 있습니다.

### 요약 {#summary}

<tldr>

Jetpack Compose는 smart recomposition을 기본으로 지원하지만, 그 효과를 누리려면 개발자가 stability 원칙에 맞춰 클래스를 설계하고 가능한 한 리컴포지션이 줄어들도록 코드를 다듬어야 합니다. stability 의 의미를 이해하고 적용하면 더 효율적이고 확장성 있는 Compose UI를 만들 수 있습니다.

</tldr>
