# 2.1 Compose Fundamentals

Android 팀이 [Jetpack Compose 1.0 stable](https://android-developers.googleblog.com/2021/07/jetpack-compose-announcement.html)을 발표한 이후, 프로덕션 환경에서의 채택이 빠르게 가속화되었습니다.
2023년까지 Google은 Jetpack Compose로 구축된 125,000개 이상의 앱이 Google Play Store에 성공적으로 게시되었다고 보고했습니다.
오늘날, Jetpack Compose는 널리 사용되는 UI 툴킷이 되어 개발자들이 선언적으로 레이아웃을 생성함으로써 생산성과 효율성을 크게 높일 수 있도록 합니다.

일부 기업들은 여전히 XML 기반 레이아웃에 의존하고 있지만, XML에서 Compose로 전환하는 것은 단숨에 이루어질 수 있는 작업이 아닙니다.
결과적으로 많은 개발자들이 여전히 두 가지 접근 방식 모두에 익숙해져야 합니다.
하지만 최근 몇 년간 생태계가 크게 성숙하여 강력한 커뮤니티 지원과 일반적인 문제에 대한 솔루션을 제공함에 따라, 대부분의 새로운 프로젝트는 Jetpack Compose를 채택하는 경향이 있습니다.

Jetpack Compose는 코드 재사용성 향상과 Lifecycle, Navigation, Hilt와 같은 기존 Android 프레임워크와의 원활한 호환성 등 주요 장점을 제공합니다.
또한 Coroutines에 대한 향상된 지원과 다양한 커뮤니티 중심 확장 기능을 포함합니다 .
이러한 이점에도 불구하고, 개발자는 성능을 최적화하고 비효율성을 방지하기 위해 recomposition과 같은 Jetpack Compose의 내부 메커니즘에 대한 깊은 이해를 얻어야 합니다.

`Jetpack Compose`는 세 가지 주요 구성 요소, 즉 `Compose Compiler`, `Compose Runtime`, `Compose UI`를 기반으로 합니다.
`remember`, `LaunchedEffect`, `Box`, `Column`, `Row`와 같이 UI 화면을 구축하는 데 사용되는 대부분의 `API`는 Runtime 및 UI 레이어에서 나옵니다.
하지만 내부적으로 `Jetpack Compose`는 라이브러리 종속성만 추가하면 프로젝트에 원활하게 통합되도록 더욱 복잡하게 구성되어 있습니다.

Compose 내부 구조에 대한 깊은 이해가 애플리케이션 구축에 필수적인 것은 아니지만, 전반적인 아키텍처를 파악하는 것은 Compose의 렌더링 단계 및 선언형 UI 개발의 본질과 같은 개념을 포함하여 다양한 역할을 이해하는 데 큰 도움이 될 수 있습니다.

이 섹션에서는 처음에는 이해하기 어려울 수 있는 `Jetpack Compose`의 고급 측면을 자세히 다룹니다.
개념이 복잡하다고 느껴진다면, 더 깊이 있는 주제를 탐색하기 전에 보다 쉽게 접근할 수 있는 진입점을 제공하는 [Compose Runtime](2-2-Compose-Runtime.md) 또는 [Compose UI](2-3-Compose-UI.md) 부터 시작하는 것을 고려해 보세요.