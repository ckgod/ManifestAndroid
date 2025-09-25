# Details: fragmentManager와 childFragmentManager의 차이점

Android에서 `fragmentManager`와 `childFragmentManager`는 Fragment 관리에 필수적이지만, 서로 다른 목적을 가지고 별개의 스코프 내에서 작동합니다.

## fragmentManager

`fragmentManager`는 `FragmentActivity` 또는 `Fragment` 자체와 연관되며, 액티비티 수준에서 Fragment를 관리하는 역할을 합니다. 여기에는 상위 액티비티에 직접 연결된 Fragment를 추가, 교체 또는 제거하는 작업이 포함됩니다.

액티비티에서 `supportFragmentManager`를 호출하면 이 `fragmentManager`에 접근하게 됩니다. `fragmentManager`에 의해 관리되는 Fragment들은 형제 관계이며 동일한 계층 수준에서 작동합니다.

```Kotlin
// Managing fragments at the activity level
supportFragmentManager.beginTransaction()
    .replace(R.id.container, ExampleFragment())
    .commit()
```

이는 일반적으로 Activity의 주요 탐색 또는 UI 구조의 일부인 Fragment에 사용됩니다.

## childFragmentManager

`childFragmentManager`는 `Fragment`에 특정되며, 자체 `child fragment`를 관리합니다.
이를 통해 `fragment`는 다른 `fragment`를 호스팅하여 중첩된 `fragment` 구조를 생성할 수 있습니다.
`childFragmentManager`를 사용할 때는 부모 `fragment`의 `lifecycle` 내에서 `fragment`를 정의합니다. 이는 `fragment` 내에 `UI`와 `logic`을 캡슐화하는 데 유용하며, 특히 `fragment`가 `Activity`의 `fragment lifecycle`과 독립적으로 자체 중첩 `fragment` 세트를 필요로 할 때 유용합니다.

```Kotlin
// Managing child fragments within a parent fragment
childFragmentManager.beginTransaction()
    .replace(R.id.child_container, ChildFragment())
    .commit()
```

`childFragmentManager`에 의해 관리되는 하위 `Fragment`는 상위 `Fragment`에 범위가 지정되며, 이는 하위 `Fragment`의 `lifecycle`이 상위 `Fragment`에 묶여 있음을 의미합니다. 예를 들어, 상위 `Fragment`가 소멸되면 해당 하위 `Fragment`도 함께 소멸됩니다.

## 주요 차이점

| 구분        | fragmentManager                                             | childFragmentManager                                                           |
|-----------|-------------------------------------------------------------|--------------------------------------------------------------------------------|
| **범위**    | `Activity` 수준에서 작동하며, `Activity`에 직접 연결된 `Fragment`를 관리합니다. | `Fragment` 내에서 작동하며, 부모 `Fragment` 내에 중첩된 `Fragment`를 관리합니다.                   |
| **사용 사례** | `Activity`의 주요 `UI` 구성 요소를 형성하는 `Fragment`에 사용합니다.          | `Fragment`가 자체 중첩 `Fragment`를 관리해야 할 경우 사용하여 더 모듈화되고 재사용 가능한 `UI` 구성 요소를 만듭니다. |
| **수명 주기** | 관리되는 `Fragment`는 `Activity`의 수명 주기를 따릅니다.                   | 관리되는 `Fragment`는 부모 `Fragment`의 수명 주기를 따릅니다.                                   |

## 요약

`fragmentManager`와 `childFragmentManager` 중 어떤 것을 선택할지는 `UI`의 계층적 구조에 따라 달라집니다. `Activity` 수준의 `Fragment` 관리를 위해서는 `fragmentManager`를 사용하세요. 부모 `Fragment` 내부에 `Fragment`를 중첩하려면 `childFragmentManager`를 선택하십시오. 이들의 스코프와 라이프사이클을 이해하는 것은 `Android` 애플리케이션의 더 나은 구성과 모듈화를 보장합니다.