PROGRAM optimized_max_subarray
  USE OMP_LIB
  IMPLICIT NONE
  
  INTEGER(8), PARAMETER :: N = 3000
  INTEGER(8), PARAMETER :: RUNS = 20
  INTEGER(8), PARAMETER :: A = 1664525_8
  INTEGER(8), PARAMETER :: C = 1013904223_8
  INTEGER(8), PARAMETER :: M32 = 4294967295_8
  INTEGER(8), PARAMETER :: MIN_VAL = -10
  INTEGER(8), PARAMETER :: MAX_VAL = 10
  INTEGER(8), PARAMETER :: RANGE_VAL = MAX_VAL - MIN_VAL + 1
  
  INTEGER(8) :: i, j, run, total_sum, run_seed, temp
  INTEGER(8) :: count_start, count_end, count_rate, count_max
  REAL(8) :: elapsed_time
  INTEGER(8), ALLOCATABLE :: arr(:)
  
  ALLOCATE(arr(N))
  total_sum = 0
  run_seed = 42_8
  
  CALL SYSTEM_CLOCK(count_start, count_rate, count_max)
  
  !$OMP PARALLEL DEFAULT(NONE) SHARED(arr, total_sum, run_seed) &
  !$OMP PRIVATE(i, j, run, temp)
  !$OMP DO REDUCTION(+:total_sum) SCHEDULE(dynamic)
  DO run = 1, RUNS
     ! Generate random numbers for this run
     temp = IAND(A * run_seed + C + run, M32)
     DO i = 1, N
        temp = IAND(A * temp + C, M32)
        arr(i) = MIN_VAL + MOD(temp, RANGE_VAL)
     END DO
     
     ! Find maximum subarray sum
     BLOCK
        INTEGER(8) :: local_max_sum, current_sum
        local_max_sum = -HUGE(0_8)
        DO i = 1, N
           current_sum = 0
           DO j = i, N
              current_sum = current_sum + arr(j)
              local_max_sum = MAX(local_max_sum, current_sum)
           END DO
        END DO
        total_sum = total_sum + local_max_sum
     END BLOCK
  END DO
  !$OMP END DO
  !$OMP END PARALLEL
  
  CALL SYSTEM_CLOCK(count_end)
  elapsed_time = REAL(count_end - count_start, 8) / REAL(count_rate, 8)
  
  PRINT '(A,I0)', "Total Maximum Subarray Sum (20 runs): ", total_sum
  PRINT '(A,F0.6,A)', "Execution Time: ", elapsed_time, " seconds"
  
  DEALLOCATE(arr)
END PROGRAM optimized_max_subarray