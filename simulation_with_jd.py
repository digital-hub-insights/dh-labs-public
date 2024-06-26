# -*- coding: utf-8 -*-
"""
simulation_with_jd.py
By Cordell L. Tanny, CFA, FRM, FDP
April 15, 2024
"""

# Import needed modules
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from scipy.stats import probplot, skew, kurtosis
import yfinance as yf

sns.set_theme()

# Initialization
# Select a start date, end date for the analysis.
start_date = '2000-01-01'
end_date = '2024-03-31'

# Create a list with the tickers to use.
tickers = ['SPY', 'IWM', 'GOVT', 'LQD', 'EFA', 'EEM', 'IGOV', 'IBND']

# retrieve the prices from yahoo finance
df_prices = yf.download(tickers, start_date, end_date)['Adj Close'].dropna()
print(df_prices.head())

# resample to monthly, and convert to returns
df_prices.index = pd.to_datetime(df_prices.index)
df_returns = df_prices.resample('M').last().pct_change().dropna()
print(df_returns.head())

# create a function that will show the histogram of monthly returns for all
# asset classes.
def plot_return_histograms(returns, stacked=False, bars=True):
    """
    Plots histograms and/or KDE of monthly returns for each asset class in the returns DataFrame.

    Parameters:
    returns (pd.DataFrame): DataFrame containing return data for various asset classes.
    stacked (bool): If True, plots all histograms overlapped on one another for comparison.
                    If False, plots histograms in a grid.
    bars (bool): If True, shows histogram bars along with the smooth KDE.
                 If False, shows only the smooth KDE without bars.
    """
    n_assets = returns.shape[1]  # Number of asset classes
    asset_names = returns.columns  # Asset class names

    if stacked:
        plt.figure(figsize=(12, 8))
        for asset_name in asset_names:
            if bars:
                sns.histplot(returns[asset_name], kde=True, stat="density", element="step", alpha=0.5, bins=30, label=asset_name)
            else:
                sns.kdeplot(returns[asset_name], bw_adjust=2, label=asset_name)
        plt.legend()
        plt.title('Overlapped Histograms of Monthly Returns')
        plt.xlabel('Returns')
        plt.ylabel('Frequency')
    else:
        # Determine the grid size
        n_rows = int(np.ceil(n_assets / 4))
        n_cols = min(n_assets, 4)

        fig, axs = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 4 * n_rows), squeeze=False)
        for i, asset_name in enumerate(asset_names):
            row, col = divmod(i, n_cols)
            ax = axs[row, col]
            if bars:
                sns.histplot(returns[asset_name], kde=True, stat="density", element="step", alpha=0.5, bins=30, ax=ax)
            else:
                sns.kdeplot(returns[asset_name], bw_adjust=2, ax=ax)
            ax.set_title(asset_name)
            ax.set_xlabel('Returns')
            ax.set_ylabel('Frequency')

        # Hide empty subplots
        for j in range(i+1, n_rows * n_cols):
            axs.flatten()[j].axis('off')

        plt.tight_layout()

    plt.show()


# create the historgram
plot_return_histograms(df_returns, stacked=True, bars=False)

# the function could also be used to show the distributions separately
plot_return_histograms(df_returns, stacked=False, bars=True)

# create a function to plot only the left tail

def plot_kde_left_tails(returns, x_max=-0.1, y_max=None):
    """
    Plots the kernel density estimation (KDE) focusing specifically on the left tails of the return distributions
    for each asset class provided in the `returns` DataFrame. This visualization helps in analyzing the
    behavior of returns at the extreme negative end up to a specified cutoff point.

    Parameters:
    - returns (pd.DataFrame): DataFrame with each column representing return data for a different asset class.
                              Each column's data is used to plot its respective KDE.
    - x_max (float, optional): The maximum x value (cutoff point) to focus on the left tail. Default is -0.1,
                               which typically focuses on the left tail of the return distributions.
    - y_max (float, optional): The maximum y value for the y-axis, allowing control over the vertical scale
                               of the plot. If not specified, the scale is determined automatically.

    The function creates a plot for each asset class's returns, overlaying their KDEs to focus on
    negative returns up to the `x_max` value. This is useful for visualizing the density and frequency
    of negative returns in different asset classes.
    """
    plt.figure(figsize=(10, 6))

    for column in returns.columns:
        sns.kdeplot(returns[column], label=column)

    plt.xlabel('Return')
    plt.ylabel('Density')
    plt.title(f'KDE of Left Tails (Up to {x_max}) for Asset Classes')
    plt.legend(frameon=False)
    plt.grid(True)
    plt.xlim(right=x_max)  # Set the maximum x value to focus on the left tail
    if y_max is not None:
        plt.ylim(top=y_max)
    plt.show()


# set the x_max to -0.1 as it looks like a good break point to examine
# the left tail. Set y_max to anything that provides enough space on the graph
# that provides detail.
plot_kde_left_tails(df_returns, x_max=-0.1, y_max=2)

# create a function to plot the q-q plots to visualize normality
def plot_qq_grid(returns):
    """
    Generates a grid of Quantile-Quantile (QQ) plots for asset returns.

    Parameters:
        returns (pd.DataFrame): DataFrame containing returns data for multiple assets.

    Returns:
        None: Displays the QQ plots directly.

    This function calculates the required number of rows and creates a grid of subplots for the QQ plots.
    Each subplot represents the QQ plot for a single asset's returns.

    Unused subplots are hidden if the number of assets is not a multiple of 4.

    Example usage:
    ```
    plot_qq_grid(returns_df)
    plt.show()
    ```
    """
    num_assets = returns.shape[1]
    num_rows = (num_assets + 3) // 4  # Calculate the required number of rows for the grid
    fig, axes = plt.subplots(num_rows, 4, figsize=(4 * 4, num_rows * 4))  # Assume each subplot is 4x4 inches
    axes = axes.flatten()  # Flatten the 2D array of axes to simplify the iteration

    for i, asset in enumerate(returns.columns):
        probplot(returns[asset].dropna(), dist="norm", plot=axes[i])
        axes[i].set_title(asset)

    # Hide any unused axes if the number of plots is not a multiple of 4
    for j in range(num_assets, len(axes)):
        fig.delaxes(axes[j])

    fig.tight_layout()
    plt.show()


plot_qq_grid(df_returns)

# isolate returns for an asset class
ac_returns = df_returns[['SPY']]

# Set the seed for reproducibility
np.random.seed(42)

# Fit a Johnson SU distribution to the data
gamma, delta, xi, lambda_ = stats.johnsonsu.fit(ac_returns)

# Sample from the Johnson SU distribution
num_samples = len(df_returns)
sampled_returns = stats.johnsonsu.rvs(gamma, delta, loc=xi, scale=lambda_,
                                      size=num_samples)

# Plotting for comparison
plt.figure(figsize=(10, 6))
plt.hist(sampled_returns, bins=50, alpha=0.6, color='g', label='Sampled')
plt.hist(ac_returns, bins=50, alpha=0.6, color='b', label='Original')
plt.legend()
plt.title("Comparison of Original and Sampled Returns")
plt.show()

# we need to write a function to calculate the annualized return for a
# given series of returns
def annualize_returns(returns, frequency='M'):
    """
    Annualizes a set of returns given a specific frequency.

    This function takes a series of returns, calculates the compounded growth over the period,
    and then annualizes these returns based on the specified frequency. The frequency determines
    the number of periods per year (e.g., 12 for monthly, 252 for daily). It is crucial for
    correctly scaling the returns to an annual basis.

    Parameters:
    returns (pd.Series or pd.DataFrame): A pandas Series or DataFrame containing the returns to be annualized.
    frequency (str): The frequency of the returns. Options: 'M' for monthly, 'D' for daily, 'Q' for quarterly.
                     Defaults to 'M'.

    Returns:
    pd.DataFrame: A DataFrame containing the annualized returns, expressed as percentages and rounded to two decimal places.
    """

    # Determine the number of periods per year based on the frequency
    if frequency == 'M':
        periods_per_year = 12
    elif frequency == 'D':
        periods_per_year = 252
    elif frequency == 'Q':
        periods_per_year = 4
    else:
        raise ValueError("Unsupported frequency. Please use 'M', 'D', or 'Q'.")

    # Calculate compounded growth and number of periods
    compounded_growth = (returns + 1).prod()
    n_periods = returns.shape[0]

    # Annualize the returns
    annualized_returns = compounded_growth ** (periods_per_year / n_periods) - 1

    # Return the annualized returns as a DataFrame
    return np.round(annualized_returns.to_frame(name='Return').mul(100), 2)


# function to run the asset class simulations
def simulate_asset_class_returns_jsu(returns, num_simulations, num_years, frequency='M', random_seed=None):
    """
    Simulate future returns for asset classes using Johnson SU distribution and compute expected returns.

    Args:
    returns (pd.DataFrame): DataFrame containing historical monthly returns for multiple asset classes.
    num_simulations (int): Number of simulations to run for each asset class.
    num_years (int): Number of years to simulate for each simulation.
    frequency (str): Frequency of returns, 'M' for monthly.
    random_seed (int, optional): Seed for the random number generator to ensure reproducibility.

    Returns:
    pd.DataFrame: DataFrame with a single column 'Expected Return', indexed by asset classes.
    """

    # Set the random seed for reproducibility
    if random_seed is not None:
        np.random.seed(random_seed)

    # Initialize a DataFrame to store expected returns
    expected_returns = pd.DataFrame(index=returns.columns, columns=['Expected Return'])

    # Loop through each asset class
    for asset in returns.columns:
        # Isolate returns for the current asset class
        ac_returns = returns[asset].dropna()

        # Fit a Johnson SU distribution to the data
        gamma, delta, xi, lambda_ = stats.johnsonsu.fit(ac_returns)

        # Initialize a list to store average annualized returns for each simulation
        avg_annualized_returns = []

        # Run simulations
        for _ in range(num_simulations):
            # Sample from the Johnson SU distribution for the entire simulation period
            sampled_returns = stats.johnsonsu.rvs(gamma, delta, loc=xi, scale=lambda_, size=num_years * 12)

            # Convert sampled returns to a DataFrame
            sampled_df = pd.DataFrame(sampled_returns, columns=['Returns'])

            # Calculate the average annualized return for this simulation using the DataFrame
            avg_annualized_return = annualize_returns(sampled_df, frequency=frequency)

            # Store the result
            avg_annualized_returns.append(avg_annualized_return)

        # Calculate the expected return for this asset class (average of averages)
        expected_returns.loc[asset, 'Expected Return'] = np.mean(avg_annualized_returns).round(2)

    return expected_returns

# simulate asset class returns
mu_jnsu = np.round(simulate_asset_class_returns_jsu(df_returns, num_simulations=2000, num_years=10, frequency='M', random_seed=42), 2)

print(mu_jnsu)

# let's compare it with historical returns
mu_historical = annualize_returns(df_returns, 'M')
print(mu_historical)

