PROGRAM max_subarray
  IMPLICIT NONE
  INTEGER(8), PARAMETER :: a = 1664525_8, c = 1013904223_8, m32 = 4294967295_8
  INTEGER(8) :: n, initial_seed, min_val, max_val, range_val, total_sum, run_seed, temp
  INTEGER(8) :: i, j, run, max_sum, current_sum
  INTEGER(8), ALLOCATABLE :: random_numbers(:)
  INTEGER :: count_start, count_end, count_rate, count_max
  REAL :: elapsed_time
  INTEGER(8) :: elapsed_ticks

  n = 3000
  initial_seed = 42
  min_val = -10
  max_val = 10
  range_val = max_val - min_val + 1
  total_sum = 0
  ALLOCATE(random_numbers(n))

  CALL SYSTEM_CLOCK(count_start, count_rate, count_max)
  run_seed = initial_seed

  DO run = 1, 20
     run_seed = IAND(a * run_seed + c, m32)
     temp = run_seed
     DO i = 1, n
        temp = IAND(a * temp + c, m32)
        random_numbers(i) = min_val + MOD(temp, range_val)
     END DO

     max_sum = -HUGE(0_8)
     DO i = 1, n
        current_sum = 0
        DO j = i, n
           current_sum = current_sum + random_numbers(j)
           IF (current_sum > max_sum) max_sum = current_sum
        END DO
     END DO
     total_sum = total_sum + max_sum
  END DO

  CALL SYSTEM_CLOCK(count_end)
  elapsed_ticks = count_end - count_start
  IF (elapsed_ticks < 0) elapsed_ticks = elapsed_ticks + count_max + 1
  elapsed_time = REAL(elapsed_ticks) / REAL(count_rate)

  PRINT '(A, I0)', "Total Maximum Subarray Sum (20 runs): ", total_sum
  PRINT '(A, F0.6, A)', "Execution Time: ", elapsed_time, " seconds"
  DEALLOCATE(random_numbers)
END PROGRAM max_subarray