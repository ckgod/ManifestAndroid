# Android Manifest Notes

이 문서는 [skydoves/manifest-android-interview](https://github.com/skydoves/manifest-android-interview) 내용을 기반으로 안드로이드 핵심 CS 지식을 학습하고 정리한 프로젝트입니다.

## 학습 목차

### 1.1 Android Framework

Android 플랫폼의 기본 구조와 핵심 개념들을 다룹니다.

- [Q1. Android란?](Q1-Android.md) - Android 운영체제의 기본 개념과 아키텍처
- [Q2. Intent](Q2-Intent.md) - 컴포넌트 간 통신을 위한 Intent 시스템
- [Q3. PendingIntent](Q3-Pending-Intent.md) - 지연 실행을 위한 PendingIntent  
- [Q4. Serializable & Parcelable](Q4-Serializable-Parcelable.md) - 객체 직렬화 방법들
  - [Details: Parcel and Parcelable](Details-Parcel-and-Parcelable.md)
- [Q5. Context](Q5-Context.md) - Android의 Context 개념과 올바른 사용법
  - [Details: 올바른 Context 사용법](Details-올바른-Context-사용법.md)
  - [Details: ContextWrapper](Details-ContextWrapper.md)
  - [Details: This vs BaseContext](Details-This-vs-BaseContext.md)
- [Q6. Application Class](Q6-Application-Class.md) - Application 클래스의 역할과 활용
- [Q7. AndroidManifest](Q7-AndroidManifest.md) - 앱 구성 정보를 담는 매니페스트 파일
- [Q8. Activity Lifecycle](Q8-Activity-LifeCycle.md) - 액티비티 생명주기 관리
  - [Details: Lifecycle 인스턴스란](Details-Lifecycle-인스턴스란.md)
  - [Details: 여러 Activity 간 수명 주기 변화](Details-여러-Activity-간-수명-주기-변화.md)
- [Q9. Fragment 생명주기](Q9-Fragment-생명주기.md) - 프래그먼트 생명주기와 관리
  - [Details: Fragment의 viewLifecycleOwner 인스턴스](Details-Fragment의-viewLifecycleOwner-인스턴스.md)
  - [Details: fragmentManager와 childFragmentManager의 차이점](Details-fragmentManager와-childFragmentManager의-차이점.md)
- [Q10. Service](Q10-Service.md) - 백그라운드 작업을 위한 Service 컴포넌트
  - [Details: Service의 생명주기](Details-Service의-생명주기.md)
  - [Details: Forground Service](Details-Forground-Service.md)
- [Q11. BroadcastReceiver](Q11-BroadcastReceiver.md) - 시스템 및 앱 이벤트 수신
- [Q12. ContentProvider](Q12-ContentProvider.md) - 앱 간 데이터 공유를 위한 ContentProvider
  - [Details: 앱 시작 시 ContentProvider 사용하여 구성을 초기화하기](Details-앱-시작-시-ContentProvider-사용하여-구성을-초기화하기.md)
- [Q13. Configuration Change](Q13-Configuration-Change.md) - 구성 변경 처리 전략

### 1.2 ETC

이 외로 추가적인 내용을 다룹니다.

- [E1. RecyclerView 렌더링 과정](E1-RecyclerView-렌더링-과정.md) - 효율적인 리스트 구현을 위한 RecyclerView
