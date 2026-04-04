# Q9) Release 모드에서의 Compose 성능 측정

## 왜 항상 release 모드에서 Compose 성능을 측정해야 하나요? {#why-release-mode}

Jetpack Compose의 성능을 측정할 때는 항상 [R8이 활성화된 release 모드](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization)에서 앱을 실행하는 것이 우선입니다. debug 모드는 인터프리터 실행, <tooltip term="JIT">JIT</tooltip> 컴파일, Live Edit Literals 같은 개발자 도구 기능을 위한 추가 오버헤드가 끼어 있어, 실제 사용자 경험을 정확히 반영하지 못하기 때문입니다.

### Debug 모드가 Compose에 끼치는 영향 {#impact-of-debug-mode}

Compose는 OS에 번들된 형태가 아니라 **라이브러리(unbundled)** 로 배포되기 때문에, debuggable 앱에서는 런타임에 인터프리트되고 컴파일됩니다. 반면 View 시스템은 Android OS에 번들되어 사전 컴파일된 상태이므로, debug 모드에서도 큰 추가 비용 없이 동작합니다. 결과적으로 같은 디버그 빌드라도 Compose 코드는 인터프리트와 JIT 컴파일의 부담을 동시에 짊어지게 되어 release 빌드와의 성능 차이가 크게 벌어집니다.

Android 팀의 설명을 빌리자면, View 라이브러리는 결국 사전 컴파일된 **release 빌드** 상태의 프레임워크 코드로 들어가 있는 반면, Compose는 lazy list 관리 같은 작은 영역만 그렇지 않고 UI 스택 전체를 debuggable 코드로 실행한다고 표현됩니다.

### Live Edit Literals와 개발자 도구 {#live-edit-literals}

Debug 빌드에서는 [Live Edit Literals](https://developer.android.com/develop/ui/compose/tooling#live-edit-literals) 같은 개발자 기능이 활성화됩니다. 이 기능은 상수를 getter 함수로 치환해 런타임 갱신을 가능하게 만드는데, 이 과정에서 추가 계산이 발생하고 일부 최적화가 막힙니다. 그 결과 debug 모드에서는 리컴포지션과 렌더링이 release 빌드보다 느려질 수밖에 없습니다.

### Release 모드에서의 R8 최적화 {#r8-in-release-mode}

[R8](https://developer.android.com/build/shrink-code)은 release 빌드에서 람다 그룹화, 소스 정보 제거, 상수 폴딩, 인터페이스 호출의 정적 호출 변환 같은 최적화를 통해 성능을 크게 개선합니다. 이런 최적화는 시작 시간을 줄이고 메모리 사용량을 낮추며 런타임 실행 흐름을 단순하게 만들어 줍니다.

Android 팀의 보고에 따르면 Compose는 R8 최적화로부터 큰 이점을 얻습니다. R8을 기본 설정으로 적용하는 것만으로도 시작 성능이 약 75%, 프레임 렌더링 성능이 약 60% 개선된 사례가 공개되어 있습니다. R8이 수행하는 다양한 최적화 가운데 Compose 코드에 가장 큰 영향을 주는 항목들은 다음과 같습니다.

- **람다 그룹화(Lambda grouping)**: 비슷한 람다 구현을 묶어 메서드 오버헤드를 줄입니다.
- **소스 정보 제거(Omitting source information)**: 디버그·소스 메타데이터를 제거해 APK 크기를 줄입니다.
- **상수 폴딩(Constant folding)**: 컴파일 시점에 상수 표현식을 정리해 런타임 효율을 올립니다.
- **인터페이스 호출의 정적 변환**: 동적 인터페이스 호출을 더 빠른 정적 메서드 호출로 바꿔 실행 속도를 끌어올립니다.

### Baseline Profile이 중요한 이유 {#why-baseline-profile}

Compose는 release 모드의 성능을 한층 더 끌어올리기 위해 [Baseline Profile](https://developer.android.com/topic/performance/baselineprofiles/overview)에 의존합니다. Baseline Profile은 Compose의 핵심 메서드를 미리 컴파일해 두어 앱 시작 시점의 인터프리트와 JIT 컴파일을 피할 수 있게 해 줍니다. Debug 빌드에서는 Baseline Profile이 사용되지 않으므로, debug에서 측정한 성능은 실제 사용자 경험을 충분히 반영하지 못합니다. 더 깊은 자료는 *Improve Your Android App Performance With Baseline Profiles* 같은 글을 참고할 수 있습니다.

### 실전 측정 권장사항 {#practical-recommendations}

Compose 앱의 실제 성능을 정확히 측정하려면 항상 R8과 Baseline Profile이 활성화된 release 모드에서 테스트해야 합니다. [Macrobenchmark](https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview) 같은 도구를 사용하면 시작 시간과 런타임 성능을 객관적으로 측정할 수 있습니다. 이 절차를 거쳐야 진짜 성능 병목을 찾아내고, 사용자에게 매끄러운 경험을 제공할 수 있습니다.

### 요약 {#summary}

<tldr>
Debug 모드에는 Jetpack Compose의 실제 성능을 왜곡시키는 오버헤드가 다수 포함되어 있어, release 모드에서의 측정이 필수입니다. R8 최적화와 Baseline Profile은 Compose 앱이 본래 설계된 성능을 발휘하도록 만들어 주는 핵심 도구이며, 현실적인 성능 벤치마킹을 위해서는 이 환경에서의 측정이 가장 신뢰할 수 있습니다. 더 깊이 있는 자료는 *Why should you always test Compose performance in release?* 글을 참고할 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Jetpack Compose 성능 최적화에서 R8은 어떤 역할을 하며, release 빌드에서 구체적으로 어떤 개선을 제공하나요?">

R8은 Compose 코드의 성능을 release 빌드에서 본격적으로 끌어올리는 핵심 최적화 단계입니다. Compose는 라이브러리 형태로 앱과 함께 배포되기 때문에, 별도의 최적화 없이 그대로 실행하면 인터프리트와 JIT 컴파일이 그대로 비용으로 따라옵니다. R8은 빌드 단계에서 사용되지 않는 코드를 제거하고 함수 호출 그래프를 평탄화하면서, Compose 런타임이 자주 거치는 경로를 더 짧고 직접적인 호출 흐름으로 바꿔 줍니다. 그 결과 같은 코드라도 실행 단계에서 거치는 분기와 인다이렉션이 줄어들어 시작 시간과 프레임 렌더링 시간이 동시에 좋아집니다.

구체적으로 영향이 큰 항목은 본문에서 정리한 네 가지입니다. **람다 그룹화** 는 Compose에서 다량으로 만들어지는 람다 구현을 비슷한 형태끼리 묶어 메서드 수와 호출 오버헤드를 줄입니다. **소스 정보 제거** 는 디버그 메타데이터를 걷어내 APK 크기와 클래스 로딩 비용을 함께 떨어뜨립니다. **상수 폴딩** 은 컴파일 시점에 결정 가능한 식을 미리 계산해 두어 런타임 분기를 줄이고, **인터페이스 호출의 정적 변환** 은 자주 호출되는 인터페이스 메서드를 더 빠른 정적 호출로 치환합니다. Compose의 컴포저블 호출 경로는 이런 인터페이스 디스패치가 빈번한 영역이라, 이 한 가지만으로도 체감 가능한 성능 향상을 만들어 냅니다.

여기에 Baseline Profile 까지 함께 적용하면 시너지가 큽니다. R8이 코드 구조 자체를 가볍게 만들어 두고, Baseline Profile 이 그 가벼운 코드 가운데 핵심 경로를 미리 AOT 컴파일해 두는 식이기 때문입니다. 결과적으로 사용자가 처음 앱을 실행해 첫 화면에 다다르는 동안 인터프리트와 JIT 워밍업을 거의 거치지 않게 되고, 이는 곧 시작 성능과 첫 인상 프레임 안정성으로 이어집니다. 그래서 Compose 성능 측정과 실제 배포 모두에서 R8 활성화는 사실상 비협상 항목으로 다뤄지는 편이 맞습니다.

</def>
</deflist>
