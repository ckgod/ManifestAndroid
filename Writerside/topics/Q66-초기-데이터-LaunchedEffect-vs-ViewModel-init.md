# Q66) 초기 데이터 로드 위치 LaunchedEffect vs. ViewModel.init()

> 참고: 이 질문은 Kotlin Coroutines 및 Jetpack Compose와 관련된 기본적인 개념을 다룹니다. 이 주제에 익숙하지 않다면, 먼저 Kotlin 및 챕터 1: Jetpack Compose 인터뷰 질문을 학습하는 것을 고려해 보세요. 나중에 이 카테고리를 다시 방문하면 더 명확하고 깊이 있는 이해를 얻는 데 도움이 될 것입니다.

Android 개발에서 자주 논의되는 주제는 Composable의 LaunchedEffect에서 초기 데이터를 로드할 것인지, 아니면 ViewModel의 init() 블록 내에서 로드할 것인지입니다.

[공식 Android 문서](https://developer.android.com/kotlin/flow/stateflow-and-sharedflow#stateflow)와 [architecture-samples GitHub 저장소](https://github.com/android/architecture-samples/blob/130f5dbebd0c7b5ba195cc08f25802ed9f0237e5/app/src/main/java/com/example/android/architecture/blueprints/todoapp/addedittask/AddEditTaskViewModel.kt#L64)의 예시는 더 나은 생명주기 관리와 구성 변경 전반에 걸친 데이터 지속성을 위해 ViewModel.init() 내에서 데이터를 로드하는 것을 일반적으로 권장합니다.

Android 커뮤니티가 일반적으로 초기 데이터를 로드하는 방식을 알아보기 위한 설문 조사가 있었습니다.
결과는 다음과 같습니다.

![voute.png](voute.png)

설문 조사 결과에서 볼 수 있듯이, 대부분의 개발자는 ViewModel.init() 내에서 초기 데이터를 로드하는 것을 선호합니다. 

경험이 풍부한 Android 커뮤니티 구성원은 LaunchedEffect와 같은 Composable 함수를 사용하는 것보다 ViewModel.init()이 더 나은 선택인 이유를 설득력 있게 설명하며, 생명주기 안정성과 영구적인 상태 관리를 강조했습니다.

한 Android 커뮤니티 구성원이 다음과 같은 의견을 공유했습니다:
> 커뮤니티 사용자 A: “Jetpack Compose UI를 기본 애플리케이션 상태 또는 데이터의 시각적 표현으로 간주한다면, 앱이 무엇을 해야 할지 UI에 의존하여 지시하는 것은 설계 결함으로 볼 수 있습니다.
> 
> 이러한 관점에서 ViewModel.init()을 사용하는 것이 LaunchedEffect 내에서 직접 데이터를 가져오는 것보다 책임 분리가 더 우수하며, 비즈니스 로직과 UI 상태 관리가 명확하게 구분되도록 보장합니다.”

반대로, 다른 사용자는 다음과 같은 관점을 공유했습니다:
> 커뮤니티 사용자 B: “저는 ViewModel.init()에만 의존하는 것이 특정 동작이 트리거되는 시점에 대한 제어를 줄이고 단위 테스트를 복잡하게 만들 수 있다고 생각합니다. 대신, ViewModel 내에서 이벤트 기반 flow를 관찰하여 지연 초기화되고 트리거될 수 있는 독립적인 함수를 정의하는 것을 선호합니다.
> 
> 이 접근 방식은 더 큰 유연성과 제어를 제공하여 LaunchedEffect와 같은 메서드나 이벤트 트리거된 작업이 데이터 로드를 더 효과적으로 관리할 수 있도록 합니다. 추가적인 장점은 ViewModel.init 블록에 전적으로 의존하는 대신, 사용자 상호작용이나 특정 이벤트에 기반하여 데이터를 다시 가져올 때 효율성이 향상된다는 것입니다. 이는 애플리케이션에서 동적이거나 상호작용적인 기능을 다룰 때 특히 유용합니다.”

## 둘 다 안티패턴: 지연 관찰(Lazy Observation) 사용

두 해결책 모두 주목할 만한 단점을 가지고 있습니다. 흥미롭게도, Google의 Android Toolkit 팀 소속인 Ian Lake은 두 접근 방식 모두 Android 개발에서 안티패턴으로 간주되며, 초기 데이터 로드 관리에 있어 더 견고한 대안이 필요하다고 지적했습니다.

![initial-data-comment.png](initial-data-comment.png)

ViewModel.init()에서 초기 데이터를 로드하는 것은 ViewModel 생성 시 의도치 않은 부작용을 일으킬 수 있으며, UI 관련 상태를 관리하는 본래의 역할에서 벗어나 생명주기 처리를 복잡하게 만듭니다.

마찬가지로, Jetpack Compose의 LaunchedEffect 내에서 데이터를 초기화하는 것은 새로운 컴포지션이 발생할 때마다 반복적으로 트리거될 수 있습니다. 이는 ViewModel의 생명주기가 일반적으로 Composable 함수의 생명주기보다 길기 때문에 발생하며, Composable이 컴포지션에 다시 진입할 때 동일한 ViewModel 인스턴스에서 동일한 비즈니스 로직이 중복으로 트리거될 수 있습니다. 이러한 생명주기 불일치는 의도치 않은 동작을 유발하고 예상되는 데이터 흐름을 방해할 수 있습니다.

이러한 우려를 해소하기 위해 Ian Lake은 지연 초기화를 위해 <tooltip term="cold_flow">cold flow</tooltip> 사용을 권장합니다.

이 접근 방식에서 flow는 수집되기 시작하면 네트워크 요청을 하거나 데이터베이스를 쿼리하는 것과 같은 비즈니스 로직을 실행합니다. 
UI 계층에서 구독자가 없을 때까지 flow는 비활성 상태를 유지하여 불필요한 작업이 수행되지 않도록 보장합니다.

## 지연 관찰을 위한 모범 사례

아래 코드 스니펫에서 볼 수 있듯이 Pokedex-Compose 프로젝트에서 이 접근 방식의 예시를 찾을 수 있습니다.

```kotlin
val pokemon = savedStateHandle.getStateFlow<Pokemon?>("pokemon", null)
val pokemonInfo: StateFlow<PokemonInfo?> =
    pokemon.filterNotNull().flatMapLatest { pokemon ->
        detailsRepository.fetchPokemonInfo(
            // ....
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = null,
    )   
```

위 코드에서 업스트림 호출(detailsRepository.fetchPokemonInfo())은 첫 번째 구독자가 flow를 수집하기 시작할 때만 트리거됩니다. 그 결과는 stateIn 메서드를 사용하여 캐시되고 상태로 변환되어 효율적인 데이터 관리와 중복 작업 최소화를 보장합니다. stateIn 메서드는 cold Flow를 hot StateFlow로 변환하며, 어떤 상태 값에 대한 업데이트를 제공하는 cold flow가 있고, 이 flow를 생성하거나 유지하는 데 비용이 많이 들지만, 가장 최근의 상태 값을 수집해야 하는 여러 구독자가 있는 상황에서 유용합니다.

궁극적으로, pokemonInfo 속성이 hot flow 190로 정의되어 있음에도 불구하고, 가장 최근에 방출된 값은 업스트림 flow의 단일 실행 인스턴스에서 옵니다. 이 인스턴스는 여러 다운스트림 구독자들 사이에서 공유되며 지연 초기화되어 효율적인 데이터 관리와 중복 실행 감소를 보장합니다.

## 요약

Android에서 초기 데이터를 로드하는 방법에는 Jetpack Compose의 LaunchedEffect, ViewModel의 init() 메서드, 또는 cold flow를 통한 지연 관찰 등 여러 가지가 있습니다. 이 논의는 효율성과 부작용 방지를 위해 cold flow를 활용하는 것을 제안하는 것으로 결론지어졌습니다. 

그러나 보편적인 해결책은 없으며, 각 프로젝트에는 고유한 요구 사항이 따릅니다. 앱의 특정 요구 사항을 이해하는 것이 가장 적합한 접근 방식을 선택하는 데 중요합니다. 이 논의는 애플리케이션의 컨텍스트에 효과적으로 적용할 수 있는 실용적인 전략을 강조합니다. 

이 주제에 관심이 있다면 [Loading Initial Data in LaunchedEffect vs. ViewModel](https://proandroiddev.com/loading-initial-data-in-launchedeffect-vs-viewmodel-f1747c20ce62)에서 더 자세히 읽어볼 수 있습니다.

> Q) Jetpack Compose에서 ViewModel.init()과 LaunchedEffect를 사용하여 초기 데이터를 로드하는 것의 장단점은 무엇이며, 어떤 상황에서 한 가지 접근 방식을 다른 것보다 선택해야 합니까? 다른 해결책을 선호한다면 무엇입니까?

> Q) cold flow를 사용한 지연 관찰이 ViewModel.init() 또는 LaunchedEffect에 비해 초기 데이터를 로드할 때 효율성을 어떻게 향상합니까? 이 접근 방식이 유익한 시나리오의 예시를 제공하십시오.