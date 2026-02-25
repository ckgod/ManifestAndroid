# Q0) Jetpack Compose 구조

## Jetpack Compose의 구조는 어떻게 구성되어 있나요? {#jetpack-compose-structure}

Jetpack Compose는 **선언형 방식**으로 네이티브 Android 애플리케이션을 구축하기 위한 현대적인 UI 툴킷입니다. 그 구조는 **Compose Compiler**, **Compose Runtime**, **Compose UI** 세 가지 핵심 컴포넌트로 이루어지며, 각각 UI 코드를 인터랙티브한 애플리케이션으로 변환하는 과정에서 중요한 역할을 담당합니다.

![compose-structure.png](compose-structure.png)

### Compose Compiler {#compose-compiler}

Compose Compiler는 Kotlin으로 작성된 선언형 UI 코드를 Jetpack Compose가 실행할 수 있는 최적화된 코드로 변환하는 역할을 담당합니다. 컴파일 중에 `@Composable` 함수를 처리하여 필요한 UI 업데이트와 리컴포지션 로직을 생성합니다.

Compose Compiler는 [KAPT](https://kotlinlang.org/docs/kapt.html)나 [KSP](https://github.com/google/ksp) 같은 기존 어노테이션 처리 도구와 달리, Kotlin 컴파일러의 **FIR(Frontend Intermediate Representation)** 단계에서 직접 동작합니다. 이를 통해 컴파일 시 더 깊은 정적 코드 분석이 가능하여 코드 생성, 리컴포지션 관리, 성능 최적화 작업을 효율적으로 수행합니다.

주요 역할:
- `@Composable` 어노테이션이 적용된 함수를 처리하여 최적화된 바이트코드를 생성합니다.
- 상태 관리, 코드 최적화, 람다 리프팅(lambda lifting)을 지원합니다.
- Kotlin 컴파일러 파이프라인과 긴밀히 통합되어 개발 효율성과 런타임 성능을 향상시킵니다.

![compose-compiler.png](compose-compiler.png)

### Compose Runtime {#compose-runtime}

Compose Runtime은 리컴포지션과 상태 관리를 지원하는 데 필요한 핵심 기능을 제공합니다. 가변 상태를 처리하고, 스냅샷을 관리하며, 애플리케이션의 상태가 변경될 때마다 UI 업데이트를 트리거합니다.

내부적으로는 **슬롯 테이블(Slot Table)** 을 사용하여 Composition의 상태를 메모이제이션합니다. 슬롯 테이블은 갭 버퍼(gap buffer) 자료구조에서 영감을 받아 UI 컴포넌트, 컴포넌트 간 관계, 관련 상태를 효율적으로 추적하며 영향을 받는 요소만 업데이트하도록 최적화된 리컴포지션을 가능하게 합니다.

주요 역할:
- **상태 관리**: `remember`를 사용하여 상태를 유지하고, 상태 변경 시 리컴포지션을 트리거합니다.
- **사이드 이펙트 관리**: `LaunchedEffect`, `DisposableEffect` 등 사이드 이펙트 핸들러를 처리합니다.
- **CompositionLocal**: 컨텍스트별 데이터를 Composition 트리 내에서 전달합니다.
- **레이아웃 노드 구성**: Compose 레이아웃 노드를 구성하여 UI 계층 구조를 효율적으로 생성합니다.

![compose-runtime.png](compose-runtime.png)

### Compose UI {#compose-ui}

Compose UI 레이어는 애플리케이션을 구축하기 위한 고수준 컴포넌트와 UI 위젯을 제공합니다. 텍스트, 버튼, 레이아웃 컨테이너 같은 기본 요소부터 커스텀 UI 컴포넌트를 구축하기 위한 고급 API까지 포함합니다.

Compose UI 라이브러리는 Compose 레이아웃 트리 구성을 단순화하는 다양한 컴포넌트를 제공하며, 이 트리는 Compose Runtime에 의해 처리됩니다. 또한 JetBrains의 **Compose Multiplatform** 지원을 통해 동일한 Compose UI 라이브러리로 Android, iOS, 데스크톱, WebAssembly 등 다양한 플랫폼에서 일관된 UI를 구현할 수 있습니다.

주요 역할:
- 텍스트, 버튼, 레이아웃 등 기본 UI 빌딩 블록을 제공합니다.
- Android UI 시스템과 통합하여 Compose 기반 UI를 네이티브 화면에 렌더링합니다.
- Compose Multiplatform을 통해 크로스플랫폼 UI 개발을 지원합니다.

![compose-ui.png](compose-ui.png)

### 요약 {#summary}

<tldr>
Jetpack Compose의 구조는 세 가지 계층으로 나뉩니다. **Compose Compiler**는 `@Composable` 함수를 최적화된 실행 코드로 변환하고, **Compose Runtime**은 슬롯 테이블을 이용한 상태 관리와 리컴포지션 엔진을 담당하며, **Compose UI**는 화면에 표시할 고수준 위젯과 레이아웃 컴포넌트를 제공합니다. 이 계층적 아키텍처는 모듈화되고 효율적이며 유지보수하기 쉬운 Android 애플리케이션 개발을 가능하게 합니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Compose Compiler의 역할은 무엇이며, KAPT나 KSP 같은 기존 어노테이션 처리기와 어떤 차이가 있나요?">

Compose Compiler는 `@Composable` 함수를 Jetpack Compose가 실행할 수 있는 최적화된 코드로 변환하는 Kotlin 컴파일러 플러그인입니다.

**KAPT/KSP와의 핵심 차이점:**

| 항목 | Compose Compiler | KAPT / KSP |
|------|-----------------|-----------|
| 동작 시점 | FIR(컴파일러 내부) 단계에서 직접 처리 | 소스 코드를 분석한 후 새 소스 생성 |
| 코드 접근 | 컴파일러 내부 IR에 접근 가능 | 소스 수준에서만 분석 가능 |
| 최적화 | 리컴포지션 최적화, 람다 리프팅 적용 | 단순 코드 생성 |
| 통합 방식 | Kotlin 컴파일러 파이프라인과 긴밀히 통합 | 외부 처리기로 동작 |

이러한 FIR 기반 접근 방식 덕분에 Compose Compiler는 더 정교한 정적 분석과 최적화를 수행하여 런타임 성능을 높일 수 있습니다.

</def>
<def title="Q) Compose Runtime은 리컴포지션과 상태를 어떻게 관리하며, 내부적으로 어떤 자료구조를 사용하나요?">

Compose Runtime은 **슬롯 테이블(Slot Table)** 을 사용하여 Composition 상태를 메모이제이션합니다.

- **슬롯 테이블**: UI 컴포넌트, 컴포넌트 간 관계, 관련 상태를 연속된 메모리 블록에 저장합니다. 갭 버퍼(gap buffer) 자료구조에서 영감을 받아 효율적인 삽입과 삭제를 지원합니다.
- **스냅샷 시스템**: 상태 읽기/쓰기를 스냅샷 격리(snapshot isolation) 방식으로 추적하여 스레드 안전성을 보장합니다.
- **리컴포지션 최적화**: 상태가 변경되면 영향을 받는 `@Composable` 함수만 선택적으로 재실행하여 불필요한 재렌더링을 방지합니다.

이 구조 덕분에 Compose는 전체 UI 트리를 다시 그리는 대신, 변경된 부분만 효율적으로 업데이트할 수 있습니다.

</def>
</deflist>
